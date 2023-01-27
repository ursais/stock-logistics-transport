# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import json

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
    partner_id = fields.Many2one("res.partner", required=True, domain=[("is_company", "=", True)])
    currency_id = fields.Many2one(
        "res.currency",
        required=True,
        default=lambda self: self.env.user.company_id.currency_id,
    )
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.user.company_id)
    invoice_partner_id = fields.Many2one(
        "res.partner", "Invoice Address", required=True, help="Invoice address for current Waybill."
    )
    partner_order_id = fields.Many2one(
        "res.partner",
        "Ordering Contact",
        required=True,
        help="The name and address of the contact who requested the order or quotation.",
    )
    move_id = fields.Many2one(
        "account.move",
        string="Invoice",
        compute="_compute_move_id",
        store=True,
    )
    move_line_ids = fields.One2many(
        "account.move.line",
        "waybill_id",
        string="Journal Items",
        readonly=True,
    )
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
    tax_totals_json = fields.Char(
        string="Invoice Totals JSON",
        compute="_compute_tax_totals_json",
        readonly=False,
    )
    amount_total = fields.Float(compute="_compute_amount_total", string="Total", store=True)
    distance_real = fields.Float(
        help="Route obtained by electronic reading", compute="_compute_distance_real", store=True
    )
    distance_route = fields.Float(
        compute="_compute_distance_route",
        string="Sum Distance",
    )
    notes = fields.Html()
    test = fields.Char(compute="_compute_waybill_lines", store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = self.env["ir.sequence"].next_by_code("tms.waybill") or _("New")
        return super().create(vals_list)

    @api.depends(
        "partner_id",
        "transportable_line_ids",
        "transportable_line_ids.quantity",
        "transportable_line_ids.transportable_id",
        "travel_ids",
        "travel_ids.route_id",
        "travel_ids.route_id.distance",
        "travel_ids.route_id.customer_factor_ids",
        "travel_ids.route_id.customer_factor_ids.factor",
        "travel_ids.route_id.customer_factor_ids.partner_id",
        "travel_ids.distance",
    )
    def _compute_waybill_lines(self):
        for rec in self:
            rec.waybill_line_ids.filtered(lambda l: l.product_id.tms_product_category == "freight").unlink()
            if not rec.partner_id or not rec.transportable_ids or not rec.travel_ids:
                continue
            price_values = rec.travel_ids.mapped("route_id.customer_factor_ids")._get_amount_and_qty(
                distance=rec.distance_route,
                distance_real=rec.distance_real,
                qty=rec.product_qty,
                weight=rec.product_weight,
                volume=rec.product_volume,
            )
            product = self.env["product.product"].search([("tms_product_category", "=", "freight")], limit=1)
            fpos = rec.partner_id.property_account_position_id
            waybill_line = [
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "product_uom_id": product.uom_id.id,
                        "sequence": 1,
                        "product_qty": price_values["quantity"],
                        "price_unit": price_values.get("amount", price_values.get("fixed_amount", 0.0)),
                        "tax_ids": [(6, 0, fpos.map_tax(product.taxes_id).ids)],
                        "name": product.name,
                    },
                )
            ]
            if price_values["amount"] and price_values["fixed_amount"]:
                waybill_line.append(
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_uom_id": product.uom_id.id,
                            "sequence": 2,
                            "product_qty": 1,
                            "price_unit": price_values["fixed_amount"],
                            "tax_ids": [(6, 0, fpos.map_tax(product.taxes_id).ids)],
                            "name": _("%(name)s - Fixed Amount", name=product.name),
                        },
                    )
                )
            rec.update(
                {
                    "waybill_line_ids": waybill_line,
                }
            )

    @api.depends("move_line_ids.move_id", "move_line_ids")
    def _compute_move_id(self):
        for rec in self:
            rec.update(
                {
                    "move_id": rec.move_line_ids.move_id.id,
                }
            )

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id:
            self.update(
                {
                    "partner_order_id": self.partner_id.child_ids.filtered(lambda r: r.type == "contact")[0].id
                    if self.partner_id.child_ids.filtered(lambda r: r.type == "contact")
                    else False,
                    "invoice_partner_id": self.partner_id.child_ids.filtered(lambda r: r.type == "invoice")[0].id
                    if self.partner_id.child_ids.filtered(lambda r: r.type == "invoice")
                    else self.partner_id,
                    "travel_ids": False,
                }
            )

    def action_invoice(self):
        if self.mapped("move_id"):
            raise UserError(_("This Waybill is already invoiced."))
        if any(rec.state in ["draft", "cancel"] for rec in self):
            raise UserError(_("You can only invoice confirmed waybills."))
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
        if not invoices:
            # move_id may be filtered depending on the user. To ensure we get all
            # invoices related to the purchase order, we read them in sudo to fill the
            # cache.
            self.sudo()._read(["move_id"])
            invoices = self.mapped("move_id")

        action = self.env["ir.actions.act_window"]._for_xml_id("account.action_move_out_invoice_type")
        # choose the view_mode accordingly
        if len(invoices) > 1:
            action["domain"] = [("id", "in", invoices.ids)]
        elif len(invoices) == 1:
            res = self.env.ref("account.view_move_form", False)
            form_view = [(res and res.id or False, "form")]
            if "views" in action:
                action["views"] = form_view + [(state, view) for state, view in action["views"] if view != "form"]
            else:
                action["views"] = form_view
            action["res_id"] = invoices.id
        else:
            action = {"type": "ir.actions.act_window_close"}
        action["context"] = {
            "no_create": True,
        }
        return action

    def _prepare_move_line(self):
        self.ensure_one()
        move_lines = []
        for line in self.waybill_line_ids:
            move_lines.append((0, 0, line._prepare_move_line_vals()))
        return move_lines

    def _prepare_move(self, ref):
        self.ensure_one()
        move = {
            "move_type": "out_invoice",
            "ref": ref,
            "company_id": self.company_id.id,
            "currency_id": self.currency_id.id,
            "partner_id": self.partner_id.id,
            "narration": self.notes,
            "invoice_line_ids": [],
        }
        return move

    @api.depends("transportable_line_ids.quantity")
    def _compute_product_qty(self):
        for rec in self:
            rec.product_qty = sum(rec.transportable_line_ids.mapped("quantity"))

    @api.depends("transportable_line_ids.transportable_product_uom_id", "transportable_line_ids.quantity")
    def _compute_product_volume(self):
        vol_categ = self.env.ref("uom.product_uom_categ_vol")
        for rec in self:
            rec.product_volume = sum(
                rec.transportable_line_ids.filtered(
                    lambda l: l.transportable_product_uom_id.category_id == vol_categ
                ).mapped("quantity")
            )

    @api.depends("transportable_line_ids.transportable_product_uom_id", "transportable_line_ids.quantity")
    def _compute_product_weight(self):
        weight_categ = self.env.ref("uom.product_uom_categ_kgm")
        for rec in self:
            rec.product_weight = sum(
                rec.transportable_line_ids.filtered(
                    lambda l: l.transportable_product_uom_id.category_id == weight_categ
                ).mapped("quantity")
            )

    @api.depends("travel_ids.route_id.distance")
    def _compute_distance_route(self):
        for rec in self:
            rec.distance_route = sum(rec.travel_ids.mapped("route_id.distance"))

    @api.depends("travel_ids.distance")
    def _compute_distance_real(self):
        for rec in self:
            rec.distance_real = sum(rec.travel_ids.mapped("distance"))

    @api.depends("waybill_line_ids.amount_untaxed")
    def _compute_amount_freight(self):
        for rec in self:
            rec.amount_freight = sum(
                rec.waybill_line_ids.filtered(lambda l: l.product_id.tms_product_category == "freight").mapped(
                    "amount_untaxed"
                )
            )

    @api.depends("waybill_line_ids.amount_untaxed")
    def _compute_amount_move(self):
        for rec in self:
            rec.amount_move = sum(
                rec.waybill_line_ids.filtered(lambda l: l.product_id.tms_product_category == "move").mapped(
                    "amount_untaxed"
                )
            )

    @api.depends("waybill_line_ids.amount_untaxed")
    def _compute_amount_highway_tolls(self):
        for rec in self:
            rec.amount_highway_tolls = sum(
                rec.waybill_line_ids.filtered(lambda l: l.product_id.tms_product_category == "tolls").mapped(
                    "amount_untaxed"
                )
            )

    @api.depends("waybill_line_ids.amount_untaxed")
    def _compute_amount_insurance(self):
        for rec in self:
            rec.amount_insurance = sum(
                rec.waybill_line_ids.filtered(lambda l: l.product_id.tms_product_category == "insurance").mapped(
                    "amount_untaxed"
                )
            )

    @api.depends("waybill_line_ids.amount_untaxed")
    def _compute_amount_other(self):
        for rec in self:
            rec.amount_other = sum(
                rec.waybill_line_ids.filtered(lambda l: l.product_id.tms_product_category == "other").mapped(
                    "amount_untaxed"
                )
            )

    @api.depends("waybill_line_ids.amount_untaxed")
    def _compute_amount_untaxed(self):
        for rec in self:
            rec.amount_untaxed = sum(rec.waybill_line_ids.mapped("amount_untaxed"))

    @api.depends("waybill_line_ids.tax_amount")
    def _compute_amount_tax(self):
        for rec in self:
            rec.amount_tax = sum(rec.waybill_line_ids.mapped("tax_amount"))

    @api.depends("amount_untaxed", "amount_tax")
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = rec.amount_untaxed + rec.amount_tax

    @api.depends(
        "partner_id", "waybill_line_ids.tax_ids", "waybill_line_ids.price_unit", "amount_total", "amount_untaxed"
    )
    def _compute_tax_totals_json(self):
        def compute_taxes(line):
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            return line.tax_ids._origin.compute_all(
                price, line.currency_id, line.product_qty, product=line.product_id, partner=rec.partner_id
            )

        account_move = self.env["account.move"]
        for rec in self:
            tax_lines_data = account_move._prepare_tax_lines_data_for_totals_from_object(
                rec.waybill_line_ids, compute_taxes
            )
            tax_totals = account_move._get_tax_totals(
                rec.partner_id, tax_lines_data, rec.amount_total, rec.amount_untaxed, rec.currency_id
            )
            rec.tax_totals_json = json.dumps(tax_totals)

    def action_approve(self):
        for rec in self:
            if not rec.travel_ids:
                raise UserError(
                    _("Could not confirm Waybill !Waybill must be assigned to a Travel before confirming.")
                )
            rec.state = "approved"

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
            waybill.write(
                {
                    "move_id": False,
                    "state": "cancel",
                }
            )


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
    product_uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="Unit of Measure",
        required=True,
    )
    price_unit = fields.Monetary(default=0.0)
    amount_untaxed = fields.Monetary(
        compute="_compute_amount_line",
        string="Subtotal",
        store=True,
    )
    amount_total = fields.Monetary(
        compute="_compute_amount_line",
        store=True,
    )
    currency_id = fields.Many2one(
        related="waybill_id.currency_id",
        store=True,
    )
    tax_amount = fields.Float(
        compute="_compute_amount_line",
        store=True,
    )
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
    company_id = fields.Many2one(
        related="waybill_id.company_id",
        store=True,
    )
    move_line_ids = fields.One2many(
        "account.move.line",
        "waybill_line_id",
        string="Journal Items",
        readonly=True,
    )

    @api.onchange("product_id")
    def _on_change_product_id(self):
        for rec in self:
            fpos = rec.waybill_id.partner_id.property_account_position_id
            rec.update(
                {
                    "tax_ids": fpos.map_tax(rec.product_id.taxes_id),
                    "name": rec.product_id.name,
                    "product_uom_id": rec.product_id.product_uom_id.id,
                    "product_qty": 1.0,
                    "price_unit": rec.product_id.lst_price,
                }
            )

    @api.depends("product_qty", "price_unit", "discount")
    def _compute_amount_line(self):
        for rec in self:
            price_discount = rec.price_unit * ((100.00 - rec.discount) / 100)
            taxes = rec.tax_ids.compute_all(
                price_unit=price_discount,
                currency=rec.waybill_id.currency_id,
                quantity=rec.product_qty,
                product=rec.product_id,
                partner=rec.waybill_id.partner_id,
            )
            rec.update(
                {
                    "amount_untaxed": taxes["total_excluded"],
                    "tax_amount": taxes["total_included"] - taxes["total_excluded"],
                    "amount_total": taxes["total_included"],
                }
            )

    def _prepare_move_line_vals(self):
        self.ensure_one()
        fpos = self.waybill_id.partner_id.property_account_position_id
        return {
            "name": self.name,
            "product_id": self.product_id.id,
            "product_uom_id": self.product_uom_id.id,
            "quantity": self.product_qty,
            "price_unit": self.price_unit,
            "tax_ids": [(6, 0, self.tax_ids.ids)],
            "account_id": self.product_id.product_tmpl_id.get_product_accounts(fpos).get("income", False).id,
            "analytic_account_id": self.analytic_account_id.id,
            "analytic_tag_ids": [(6, 0, self.analytic_tag_ids.ids)],
            "waybill_line_id": self.id,
        }


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
    transportable_product_uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="Unit of Measure ",
        required=True,
    )
    quantity = fields.Float(
        string="Quantity (UoM)",
        required=True,
        default=0.0,
    )
    notes = fields.Html()
    waybill_id = fields.Many2one(
        comodel_name="tms.waybill",
        required=True,
        ondelete="cascade",
        readonly=True,
    )
    sequence = fields.Integer(default=10)

    @api.onchange("transportable_id")
    def _onchange_transportable_id(self):
        self.update(
            {
                "name": self.transportable_id.name,
                "transportable_product_uom_id": self.transportable_id.product_uom_id.id,
            }
        )
