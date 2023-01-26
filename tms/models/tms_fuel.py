# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class TmsFuel(models.Model):
    _name = "tms.fuel"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Fuel Logs"
    _order = "date desc,unit_id desc"

    name = fields.Char(readonly=True, copy=False)
    travel_id = fields.Many2one("tms.travel", required=True)
    # expense_id = fields.Many2one("tms.expense")
    driver_id = fields.Many2one(
        related="travel_id.driver_id",
        store=True,
    )
    unit_id = fields.Many2one(
        related="travel_id.unit_id",
        store=True,
    )
    date = fields.Date(
        required=True,
        default=fields.Date.today,
        tracking=True,
    )
    product_uom_id = fields.Many2one(
        "uom.uom",
        string="UoM",
        required=True,
        tracking=True,
    )
    product_qty = fields.Float(
        string="Quantity",
        default=1.0,
        tracking=True,
        required=True,
    )
    tax_amount = fields.Float(
        compute="_compute_amounts",
        store=True,
    )
    tax_ids = fields.Many2many(
        "account.tax",
        string="Taxes",
        domain=[("type_tax_use", "=", "purchase")],
        tracking=True,
    )
    price_total = fields.Float(
        string="Total",
        compute="_compute_amounts",
        store=True,
    )
    price_unit = fields.Float(
        string="Unit Price",
        tracking=True,
        required=True,
    )
    price_subtotal = fields.Float(
        string="Subtotal",
        compute="_compute_amounts",
        store=True,
    )
    payment_state = fields.Selection(
        related="move_id.payment_state",
        store=True,
    )
    notes = fields.Html()
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("approved", "Approved"),
            ("closed", "Closed"),
            ("cancel", "Cancelled"),
        ],
        readonly=True,
        tracking=True,
        default="draft",
        required=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        required=True,
        domain=[("is_company", "=", True)],
    )
    product_id = fields.Many2one(
        "product.product",
        string="Product",
        domain=[("tms_product_category", "=", "fuel")],
        required=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        default=lambda self: self.env.user.company_id.currency_id,
    )
    ref = fields.Char()
    # created_from_expense = fields.Boolean(readonly=True)
    # expense_line_id = fields.Many2one("tms.expense.line", readonly=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.user.company_id,
    )
    analytic_account_id = fields.Many2one(
        "account.analytic.account",
        string="Analytic Account",
        check_company=True,
    )
    analytic_tag_ids = fields.Many2many(
        "account.analytic.tag",
        string="Analytic Tags",
        check_company=True,
    )
    move_id = fields.Many2one(
        "account.move",
        string="Invoice",
        compute="_compute_move_id",
        store=True,
    )
    move_line_ids = fields.One2many(
        "account.move.line",
        "fuel_id",
        string="Journal Items",
        readonly=True,
    )

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            fpos = self.partner_id.property_account_position_id
            self.update(
                {
                    "product_uom_id": self.product_id.product_uom_id.id,
                    "tax_ids": fpos.map_tax(self.product_id.supplier_taxes_id),
                    "price_unit": self.product_id.standard_price,
                }
            )

    @api.depends("product_qty", "price_unit", "product_id")
    def _compute_amounts(self):
        for rec in self:
            rec.price_subtotal = rec.product_qty * rec.price_unit
            taxes = rec.tax_ids.compute_all(
                price_unit=rec.price_unit,
                currency=rec.currency_id,
                quantity=rec.product_qty,
                product=rec.product_id,
                partner=rec.partner_id,
            )
            rec.tax_amount = sum(t.get("amount", 0.0) for t in taxes.get("taxes", []))
            rec.price_total = rec.price_subtotal + rec.tax_amount

    @api.depends("move_line_ids.move_id", "move_line_ids")
    def _compute_move_id(self):
        for rec in self:
            rec.update(
                {
                    "move_id": rec.move_line_ids.move_id.id,
                }
            )

    def action_approve(self):
        for rec in self:
            rec.state = "approved"

    def action_cancel(self):
        if self.mapped("move_id"):
            raise UserError(_("Could not cancel Fuel Voucher! This Fuel Voucher is already Invoiced"))
        for rec in self:
            if rec.travel_id and rec.travel_id.state == "closed":
                raise UserError(
                    _("Could not cancel Fuel Voucher! This Fuel Voucher is already linked to a Travel Expense")
                )
            rec.state = "cancel"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = self.env["ir.sequence"].next_by_code("tms.fuel") or _("New")
        return super().create(vals_list)

    def action_back_to_draft(self):
        for rec in self:
            rec.state = "draft"

    def action_invoice(self):
        if self.mapped("move_id"):
            raise UserError(_("Could not Invoice Fuel Voucher! This Fuel Voucher is already Invoiced"))
        if any(rec.state in ["draft", "cancel"] for rec in self):
            raise UserError(_("Could not Invoice Fuel Voucher! This Fuel Voucher must be approved or closed"))
        invoice_batch = {}
        for rec in self:
            ref = " ".join(
                self.filtered(lambda r: r.currency_id == rec.currency_id and r.partner_id == rec.partner_id).mapped(
                    "name"
                )
            )
            invoice_batch.setdefault(rec.currency_id, {}).setdefault(rec.partner_id, rec._prepare_move(ref))[
                "invoice_line_ids"
            ].extend(rec._prepare_move_line())
        invoice_to_create = []
        for partners in invoice_batch.values():
            for data in partners.values():
                invoice_to_create.append(data)
        invoices = self.env["account.move"].create(invoice_to_create)
        return self.action_view_invoice(invoices)

    def action_view_invoice(self, invoices=False):
        """This function returns an action that display existing vendor bills of
        given fuel ids. When only one found, show the vendor bill
        immediately.
        """
        if not invoices:
            # move_id may be filtered depending on the user. To ensure we get all
            # invoices related to the purchase order, we read them in sudo to fill the
            # cache.
            self.sudo()._read(["move_id"])
            invoices = self.move_id

        result = self.env["ir.actions.act_window"]._for_xml_id("account.action_move_in_invoice_type")
        # choose the view_mode accordingly
        if len(invoices) > 1:
            result["domain"] = [("id", "in", invoices.ids)]
        elif len(invoices) == 1:
            res = self.env.ref("account.view_move_form", False)
            form_view = [(res and res.id or False, "form")]
            if "views" in result:
                result["views"] = form_view + [(state, view) for state, view in result["views"] if view != "form"]
            else:
                result["views"] = form_view
            result["res_id"] = invoices.id
        else:
            result = {"type": "ir.actions.act_window_close"}

        return result

    def _prepare_move_line_vals(self):
        self.ensure_one()
        fpos = self.partner_id.property_account_position_id
        return {
            "name": self.name,
            "product_id": self.product_id.id,
            "product_uom_id": self.product_uom_id.id,
            "quantity": self.product_qty,
            "price_unit": self.price_unit,
            "tax_ids": [(6, 0, self.tax_ids.ids)],
            "account_id": self.product_id.product_tmpl_id.get_product_accounts(fpos).get("expense", False).id,
            "analytic_account_id": self.analytic_account_id.id,
            "analytic_tag_ids": [(6, 0, self.analytic_tag_ids.ids)],
            "fuel_id": self.id,
        }

    def _prepare_move_line(self):
        self.ensure_one()
        return [(0, 0, self._prepare_move_line_vals())]

    def _prepare_move(self, ref):
        self.ensure_one()
        move = {
            "move_type": "in_invoice",
            "ref": ref,
            "date": self.date,
            "company_id": self.company_id.id,
            "currency_id": self.currency_id.id,
            "partner_id": self.partner_id.id,
            "invoice_line_ids": [],
            "narration": self.notes,
        }
        return move

    @api.constrains("product_qty", "price_total")
    def _check_amounts(self):
        for rec in self:
            if rec.product_qty <= 0:
                raise UserError(_("Liters must be greater than zero."))
            if rec.price_unit <= 0:
                raise UserError(_("Unit Price must be greater than zero."))