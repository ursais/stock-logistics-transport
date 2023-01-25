# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class TmsWaybill(models.Model):
    _name = "tms.waybill"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Waybills"
    _order = "name desc"

    transportable_line_ids = fields.One2many(
        "tms.waybill.transportable.line", "waybill_id", string="Transportable", copy=True
    )
    name = fields.Char(readonly=True, copy=False)
    travel_ids = fields.Many2many("tms.travel", copy=False, string="Travels")
    state = fields.Selection(
        [("draft", "Pending"), ("approved", "Approved"), ("cancel", "Cancelled")],
        readonly=True,
        tracking=True,
        help="Gives the state of the Waybill.",
        default="draft",
    )
    date = fields.Datetime(required=True, default=fields.Datetime.now, copy=False)
    user_id = fields.Many2one("res.users", "Salesman", default=(lambda self: self.env.user), required=True, copy=False)
    partner_id = fields.Many2one("res.partner", required=True)
    currency_id = fields.Many2one(
        "res.currency",
        required=True,
        default=lambda self: self.env.user.company_id.currency_id,
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
    move_id = fields.Many2one("account.move", readonly=True, copy=False)
    payment_state = fields.Selection(
        related="move_id.payment_state",
        store=True,
        help="Payment State of the Waybill",
    )
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

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        if self.partner_id:
            partner = self.partner_id.address_get(["invoice", "contact"])
            self.partner_order_id = partner.get("contact", False)
            self.partner_move_id = partner.get("invoice", False)

    def action_approve(self):
        for waybill in self:
            waybill.state = "approved"

    def action_view_invoice(self):
        invoices = self.mapped("move_id")
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
                raise UserError(
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
                raise UserError(_("Could not set to draft this Waybill !Travel is Cancelled !!!"))
            waybill.state = "draft"

    def action_cancel(self):
        for waybill in self:
            if waybill.move_id and waybill.move_id.state != "cancel":
                raise UserError(
                    _(
                        "You cannot unlink the invoice of this waybill"
                        " because the invoice is still valid, "
                        "please check it."
                    )
                )
            waybill.move_id = False
            waybill.state = "cancel"


class TmsWaybillLine(models.Model):
    _name = "tms.waybill.line"
    _description = "Waybill Line"
    _order = "sequence, id desc"

    waybill_id = fields.Many2one(
        comodel_name="tms.waybill",
        readonly=True,
        ondelete="cascade",
    )
    name = fields.Char(
        string="Description",
        required=True,
    )
    sequence = fields.Integer(
        help="Gives the sequence order when displaying a list of waybill lines.",
        default=10,
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        required=True,
    )
    unit_price = fields.Float(default=0.0)
    price_subtotal = fields.Float(
        compute="_compute_amount_line",
        string="Subtotal",
    )
    tax_amount = fields.Float(compute="_compute_amount_line")
    tax_ids = fields.Many2many(
        comodel_name="account.tax",
        string="Taxes",
        domain='[("type_tax_use", "=", "sale")]',
    )
    product_qty = fields.Float(
        string="Quantity",
        default=1.0,
    )
    discount = fields.Float(
        string="Discount (%)",
        help="Please use 99.99 format...",
    )
    account_id = fields.Many2one(
        "account.account",
    )

    @api.onchange("product_id")
    def on_change_product_id(self):
        for rec in self:
            fpos = rec.waybill_id.partner_id.property_account_position_id
            fpos_tax_ids = fpos.map_tax(rec.product_id.taxes_id)
            rec.update(
                {
                    "account_id": rec.product_id.property_account_income_id.id,
                    "tax_ids": fpos_tax_ids,
                    "name": rec.product_id.name,
                }
            )

    @api.depends("product_qty", "unit_price", "discount")
    def _compute_amount_line(self):
        for rec in self:
            price_discount = rec.unit_price * ((100.00 - rec.discount) / 100)
            taxes = rec.tax_ids.compute_all(
                price_unit=price_discount,
                currency=rec.waybill_id.currency_id,
                quantity=rec.product_qty,
                product=rec.product_id,
                partner=rec.waybill_id.partner_id,
            )
            rec.update(
                {
                    "price_subtotal": taxes["total_excluded"],
                    "tax_amount": taxes["total_included"] - taxes["total_excluded"],
                }
            )


class TmsWaybillTransportableLine(models.Model):
    _name = "tms.waybill.transportable.line"
    _description = "Shipped Product"
    _order = "sequence, id desc"

    transportable_id = fields.Many2one(
        comodel_name="tms.transportable",
        required=True,
    )
    name = fields.Char(
        string="Description",
        required=True,
    )
    transportable_uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="Unit of Measure ",
        required=True,
    )
    quantity = fields.Float(
        string="Quantity (UoM)",
        required=True,
        default=0.0,
    )
    notes = fields.Char()
    waybill_id = fields.Many2one(
        comodel_name="tms.waybill",
        required=True,
        ondelete="cascade",
        readonly=True,
    )
    sequence = fields.Integer(help="Gives the sequence order when displaying a list of sales order lines.", default=10)

    @api.onchange("transportable_id")
    def _onchange_transportable_id(self):
        self.update(
            {
                "name": self.transportable_id.name,
                "transportable_uom_id": self.transportable_id.uom_id.id,
            }
        )
