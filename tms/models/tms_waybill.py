# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from __future__ import division

import logging

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)
try:
    from num2words import num2words
except ImportError:
    _logger.debug("Cannot `import num2words`.")


class TmsWaybill(models.Model):
    _name = "tms.waybill"
    _inherit = "mail.thread"
    _description = "Waybills"
    _order = "name desc"

    rate = fields.Float(compute="_compute_rate", digits=(12, 4), groups="base.group_multi_currency")
    customer_factor_ids = fields.One2many(
        "tms.factor",
        "waybill_id",
        string="Waybill Customer Charge Factors",
        domain=[
            ("category", "=", "customer"),
        ],
    )
    driver_factor_ids = fields.One2many(
        "tms.factor",
        "waybill_id",
        string="Travel Driver Payment Factors",
        domain=[
            ("category", "=", "driver"),
        ],
    )
    transportable_line_ids = fields.One2many("tms.waybill.transportable.line", "waybill_id", string="Transportable")
    tax_line_ids = fields.One2many("tms.waybill.taxes", "waybill_id", string="Tax Lines", store=True)
    name = fields.Char()
    travel_ids = fields.Many2many("tms.travel", copy=False, string="Travels")
    state = fields.Selection(
        [("draft", "Pending"), ("approved", "Approved"), ("confirmed", "Confirmed"), ("cancel", "Cancelled")],
        readonly=True,
        tracking=True,
        help="Gives the state of the Waybill.",
        default="draft",
    )
    date_order = fields.Datetime("Date", required=True, default=fields.Datetime.now)
    user_id = fields.Many2one("res.users", "Salesman", default=(lambda self: self.env.user))
    partner_id = fields.Many2one("res.partner", required=True, change_default=True)
    currency_id = fields.Many2one(
        "res.currency", required=True, default=lambda self: self.env.user.company_id.currency_id
    )
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.user.company_id)
    partner_invoice_id = fields.Many2one(
        "res.partner", "Invoice Address", required=True, help="Invoice address for current Waybill."
    )
    partner_order_id = fields.Many2one(
        "res.partner",
        "Ordering Contact",
        required=True,
        help="The name and address of the contact who requested the order or quotation.",
    )
    departure_address_id = fields.Many2one(
        "res.partner", required=True, help="Departure address for current Waybill.", change_default=True
    )
    arrival_address_id = fields.Many2one(
        "res.partner", required=True, help="Arrival address for current Waybill.", change_default=True
    )
    upload_point = fields.Char(change_default=True)
    download_point = fields.Char(change_default=True)
    invoice_id = fields.Many2one("account.move", readonly=True, copy=False)
    invoice_paid = fields.Boolean(compute="_compute_invoice_paid", readonly=True)
    waybill_line_ids = fields.One2many("tms.waybill.line", "waybill_id", string="Waybill Lines")
    transportable_ids = fields.One2many("tms.waybill.transportable.line", "waybill_id", string="Shipped Products")
    product_qty = fields.Float(compute="_compute_product_qty", string="Sum Qty")
    product_volume = fields.Float(compute="_compute_product_volume", string="Sum Volume")
    product_weight = fields.Float(compute="_compute_product_weight", string="Sum Weight")
    amount_freight = fields.Float(compute="_compute_amount_freight", string="Freight")
    amount_move = fields.Float(compute="_compute_amount_move", string="Moves")
    amount_highway_tolls = fields.Float(compute="_compute_amount_highway_tolls", string="Highway Tolls")
    amount_insurance = fields.Float(compute="_compute_amount_insurance", string="Insurance")
    amount_other = fields.Float(compute="_compute_amount_other", string="Other")
    amount_untaxed = fields.Float(compute="_compute_amount_untaxed", string="SubTotal", store=True)
    amount_tax = fields.Float(compute="_compute_amount_tax", string="Taxes")
    amount_total = fields.Float(compute="_compute_amount_total", string="Total", store=True)
    distance_real = fields.Float(help="Route obtained by electronic reading")
    distance_route = fields.Float(
        compute="_compute_distance_route",
        string="Sum Distance",
    )
    notes = fields.Html()

    @api.depends("date_order")
    def _compute_rate(self):
        company_currency = self.env.company.currency_id
        for record in self.filtered(lambda r: r.date_order):
            currency = record.currency_id.with_context(date=record.date_order)
            record.rate = currency.compute(1, company_currency, round=False)

    @api.model
    def create(self, values):
        waybill = super().create(values)
        waybill.name = self.env["ir.sequence"].next_by_code("tms.waybill") or _("New")
        product = self.env["product.product"].search([("tms_product_category", "=", "freight")], limit=1)
        if product:
            self.waybill_line_ids.create(
                {
                    "tax_ids": [(6, 0, product.taxes_id.ids)],
                    "name": product.name,
                    "waybill_id": waybill.id,
                    "product_id": product.id,
                    "unit_price": waybill._compute_line_unit_price(),
                    "account_id": product.property_account_income_id.id,
                }
            )
        waybill.onchange_waybill_line_ids()
        return waybill

    def write(self, values):
        for rec in self:
            if values.get("partner_id"):
                for travel in rec.travel_ids:
                    travel.partner_ids = False
                    travel._compute_partner_ids()
            return super().write(values)

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        if self.partner_id:
            self.partner_order_id = self.partner_id.address_get(["invoice", "contact"]).get("contact", False)
            self.partner_invoice_id = self.partner_id.address_get(["invoice", "contact"]).get("invoice", False)

    def action_approve(self):
        for waybill in self:
            waybill.state = "approved"

    def action_view_invoice(self):
        invoices = self.mapped("invoice_id")
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        if len(invoices) > 1:
            action["domain"] = [("id", "in", invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref("account.view_move_form").id, "form")]
            if "views" in action:
                action["views"] = form_view + [(state, view) for state, view in action["views"] if view != "form"]
            else:
                action["views"] = form_view
            action["res_id"] = invoices.id
        else:
            action = {"type": "ir.actions.act_window_close"}

        context = {
            "default_move_type": "out_invoice",
        }
        if len(self) == 1:
            context.update(
                {
                    "default_partner_id": self.partner_id.id,
                    "default_partner_shipping_id": self.arrival_address_id.id,
                    "default_invoice_payment_term_id": self.partner_id.property_payment_term_id.id
                    or self.env["account.move"]
                    .default_get(["invoice_payment_term_id"])
                    .get("invoice_payment_term_id"),
                    "default_invoice_origin": self.name,
                    "default_user_id": self.user_id.id,
                }
            )
        action["context"] = context
        return action

    @api.depends("invoice_id")
    def _compute_invoice_paid(self):
        for rec in self:
            paid = rec.invoice_id and rec.invoice_id.payment_state in ["in_payment", "paid"]
            rec.invoice_paid = paid

    @api.onchange("customer_factor_ids", "transportable_line_ids")
    def _onchange_waybill_line_ids(self):
        for rec in self:
            rec.waybill_line_ids.filtered(lambda l: l.product_id.tms_product_category == "freight").write(
                {
                    "unit_price": rec._compute_line_unit_price(),
                }
            )

    @api.depends("transportable_line_ids.quantity")
    def _compute_product_qty(self):
        for rec in self:
            rec.product_qty = sum(rec.transportable_line_ids.mapped("quantity"))

    @api.depends("transportable_line_ids.transportable_uom_id", "transportable_line_ids.quantity")
    def _compute_product_volume(self):
        vol_categ = self.env.ref("uom.product_uom_categ_vol")
        for rec in self:
            rec.product_volume = sum(
                rec.transportable_line_ids.filtered(lambda l: l.transportable_uom_id.category_id == vol_categ).mapped(
                    "quantity"
                )
            )

    @api.depends("transportable_line_ids.transportable_uom_id", "transportable_line_ids.quantity")
    def _compute_product_weight(self):
        weight_categ = self.env.ref("uom.product_uom_categ_kgm")
        for rec in self:
            rec.product_weight = sum(
                rec.transportable_line_ids.filtered(
                    lambda l: l.transportable_uom_id.category_id == weight_categ
                ).mapped("quantity")
            )

    @api.depends("travel_ids.route_id.distance")
    def _compute_distance_route(self):
        for rec in self:
            rec.distance_route = sum(rec.travel_ids.mapped("route_id.distance"))

    def _compute_line_unit_price(self):
        for rec in self:
            return sum(
                factor.get_amount(
                    distance=rec.distance_route,
                    distance_real=rec.distance_real,
                    income=rec.amount_total,
                    qty=rec.product_qty,
                    weight=rec.product_weight,
                    volume=rec.product_volume,
                )
                for factor in rec.customer_factor_ids
            )

    @api.depends("waybill_line_ids.price_subtotal")
    def _compute_amount_freight(self):
        for rec in self:
            rec.amount_freight = sum(
                rec.waybill_line_ids.filtered(lambda l: l.product_id.tms_product_category == "freight").mapped(
                    "price_subtotal"
                )
            )

    @api.depends("waybill_line_ids.price_subtotal")
    def _compute_amount_move(self):
        for rec in self:
            rec.amount_move = sum(
                rec.waybill_line_ids.filtered(lambda l: l.product_id.tms_product_category == "move").mapped(
                    "price_subtotal"
                )
            )

    @api.depends("waybill_line_ids.price_subtotal")
    def _compute_amount_highway_tolls(self):
        for rec in self:
            rec.amount_highway_tolls = sum(
                rec.waybill_line_ids.filtered(lambda l: l.product_id.tms_product_category == "tolls").mapped(
                    "price_subtotal"
                )
            )

    @api.depends("waybill_line_ids.price_subtotal")
    def _compute_amount_insurance(self):
        for rec in self:
            rec.amount_insurance = sum(
                rec.waybill_line_ids.filtered(lambda l: l.product_id.tms_product_category == "insurance").mapped(
                    "price_subtotal"
                )
            )

    @api.depends("waybill_line_ids.price_subtotal")
    def _compute_amount_other(self):
        for rec in self:
            rec.amount_other = sum(
                rec.waybill_line_ids.filtered(lambda l: l.product_id.tms_product_category == "other").mapped(
                    "price_subtotal"
                )
            )

    @api.depends("waybill_line_ids.price_subtotal")
    def _compute_amount_untaxed(self):
        for rec in self:
            rec.amount_untaxed = sum(rec.waybill_line_ids.mapped("price_subtotal"))

    @api.depends("waybill_line_ids.tax_amount")
    def _compute_amount_tax(self):
        for rec in self:
            rec.amount_tax = sum(rec.waybill_line_ids.mapped("tax_amount"))

    @api.depends("amount_untaxed", "amount_tax")
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = rec.amount_untaxed + rec.amount_tax

    def action_confirm(self):
        for rec in self:
            if not rec.travel_ids:
                raise exceptions.ValidationError(
                    _("Could not confirm Waybill !Waybill must be assigned to a Travel before confirming.")
                )
            rec.state = "confirmed"

    @api.onchange("waybill_line_ids")
    def onchange_waybill_line_ids(self):
        for rec in self:
            tax_grouped = {}
            for line in rec.waybill_line_ids:
                unit_price = line.unit_price * (1 - (line.discount or 0.0) / 100.0)
                taxes = line.tax_ids.compute_all(
                    price_unit=unit_price,
                    currency=rec.currency_id,
                    quantity=line.product_qty,
                    product=line.product_id,
                    partner=rec.partner_id,
                )
                for tax in taxes["taxes"]:
                    tax_id = tax["id"] if isinstance(tax["id"], int) else tax["id"].origin
                    tax_grouped.setdefault(tax_id, (0, 0, {"tax_id": tax_id}))[2]["tax_amount"] = tax["amount"]
            tax_lines = [(5, 0, 0)]
            for tax in tax_grouped.values():
                tax_lines.append(tax)
            rec.update(
                {
                    "tax_line_ids": tax_lines,
                }
            )

    def action_cancel_draft(self):
        for waybill in self:
            travel = waybill.travel_ids.filtered(lambda t: t.state == "cancel")
            if travel:
                raise exceptions.ValidationError(_("Could not set to draft this Waybill !Travel is Cancelled !!!"))
            waybill.state = "draft"

    def action_cancel(self):
        for waybill in self:
            if waybill.invoice_id and waybill.invoice_id.state != "cancel":
                raise exceptions.ValidationError(
                    _(
                        "You cannot unlink the invoice of this waybill"
                        " because the invoice is still valid, "
                        "please check it."
                    )
                )
            waybill.invoice_id = False
            waybill.state = "cancel"

    def _amount_to_text(self, amount_total, currency, partner_lang="es_MX"):
        total = str(int(amount_total))
        decimals = str(float(amount_total)).split(".")[1]
        currency_type = "M.N."
        if partner_lang != "es_MX":
            total = num2words(float(amount_total)).upper()
        else:
            total = num2words(float(total), lang="es").upper()
        if currency != "MXN":
            currency_type = "M.E."
        else:
            currency = "PESOS"
        return "%s %s %s/100 %s" % (total, currency, decimals or 0.0, currency_type)
