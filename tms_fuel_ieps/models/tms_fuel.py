# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class TmsFuel(models.Model):
    _inherit = "tms.fuel"

    partner_country_code = fields.Char(
        related="partner_id.country_id.code",
        string="Country Code",
    )
    amount_ieps = fields.Monetary(
        string="IEPS Amount",
        compute="_compute_amount_ieps",
        store=True,
    )
    tax_amount_ieps = fields.Monetary(
        string="IEPS Tax Amount",
    )
    amount_untaxed_ieps = fields.Monetary(
        string="IEPS Untaxed Amount",
        compute="_compute_amounts_ieps",
        store=True,
    )
    price_unit_ieps = fields.Float(
        string="IEPS Unit Price", compute="_compute_amounts_ieps", store=True, digits="Fuel Price"
    )
    amount_total_ieps = fields.Monetary(
        string="IEPS Total Amount",
    )

    @api.depends("partner_id", "amount_total_ieps", "tax_amount_ieps", "product_qty")
    def _compute_amounts_ieps(self):
        for rec in self:
            values = {
                "amount_untaxed_ieps": 0.0,
                "price_unit_ieps": 0.0,
                "amount_ieps": 0.0,
            }
            if rec.partner_country_code and rec.partner_country_code != "MX":
                rec.update(values)
                continue
            if rec.tax_amount_ieps:
                values["amount_untaxed_ieps"] = rec.tax_amount_ieps / 0.16
            if values.get("amount_untaxed_ieps") and rec.amount_total_ieps and rec.tax_amount_ieps:
                values["amount_ieps"] = rec.amount_total_ieps - values["amount_untaxed_ieps"] - rec.tax_amount_ieps
            if rec.product_qty and values.get("amount_untaxed_ieps") > 0:
                values["price_unit_ieps"] = values["amount_untaxed_ieps"] / rec.product_qty
            rec.update(values)

    @api.depends("product_qty", "price_unit", "product_id", "partner_id", "amount_ieps")
    def _compute_amounts(self):
        return super()._compute_amounts()

    def _get_special_tax_amount(self):
        self.ensure_one()
        res = super()._get_special_tax_amount()
        if self.partner_country_code and self.partner_country_code != "MX":
            return res
        return res + self.amount_ieps

    @api.onchange("price_unit_ieps")
    def _onchange_price_unit_ieps(self):
        self.price_unit = self.price_unit_ieps

    def _prepare_move_line(self):
        res = super()._prepare_move_line()
        if self.partner_country_code and self.partner_country_code != "MX":
            return res
        vals = self._prepare_move_line_vals()
        vals.update(
            {
                "name": vals["name"] + " IEPS",
                "price_unit": self.amount_ieps,
                "quantity": 1.0,
                "account_id": self.company_id.ieps_account_id.id,
                "tax_ids": [],
            }
        )
        res.append((0, 0, vals))
        return res
