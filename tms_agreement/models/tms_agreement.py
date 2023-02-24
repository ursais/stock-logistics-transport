# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, fields, models


class TmsAgreement(models.Model):
    _name = "tms.agreement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Agreements"

    name = fields.Char(readonly=True, copy=False)
    description = fields.Char(required=True, tracking=True)
    partner_id = fields.Many2one("res.partner", string="Customer", required=True, tracking=True)
    invoice_partner_id = fields.Many2one("res.partner", string="Invoice Address", required=True, tracking=True)
    partner_order_id = fields.Many2one("res.partner", string="Ordering Contact", required=True, tracking=True)
    transportable_id = fields.Many2one("tms.transportable", string="Transportable", required=True, tracking=True)
    route_id = fields.Many2one("tms.route", string="Route", required=True, tracking=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        tracking=True,
        default=lambda self: self.env.user.company_id.currency_id,
    )
    fuel_ids = fields.One2many("tms.fuel", "agreement_id", string="Related Fuel Logs", readonly=True)
    advance_ids = fields.One2many("tms.advance", "agreement_id", string="Related Advances", readonly=True)
    travel_ids = fields.One2many("tms.travel", "agreement_id", string="Related Travels", readonly=True)
    waybill_ids = fields.One2many("tms.waybill", "agreement_id", string="Related Waybills", readonly=True)
    agreement_fuel_ids = fields.One2many("tms.agreement.fuel", "agreement_id", string="Fuel")
    agreement_advance_ids = fields.One2many("tms.agreement.advance", "agreement_id", string="Advances")
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed"), ("cancel", "Cancelled")],
        default="draft",
        required=True,
        tracking=True,
    )
    date_start = fields.Date(string="Start Date")
    date_end = fields.Date(string="End Date")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one("res.company", string="Company", required=True, default=lambda self: self.env.company)
    notes = fields.Html()

    def action_confirm(self):
        self.state = "confirmed"

    def action_cancel(self):
        self.state = "cancel"

    def action_draft(self):
        self.state = "draft"

    def action_create_documents(self):
        self.ensure_one()
        return {
            "name": "Create Documents",
            "type": "ir.actions.act_window",
            "res_model": "tms.agreement.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_agreement_id": self.id},
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = self.env["ir.sequence"].next_by_code("tms.agreement") or _("New")
        return super().create(vals_list)


class TmsAgreementFuel(models.Model):
    _name = "tms.agreement.fuel"
    _description = "Agreement Fuel"

    agreement_id = fields.Many2one("tms.agreement", readonly=True, ondelete="cascade", required=True)
    partner_id = fields.Many2one("res.partner", string="Supplier", required=True, domain=[("is_company", "=", True)])
    product_id = fields.Many2one(
        "product.product", string="Product", domain=[("tms_product_category", "=", "fuel")], required=True
    )
    product_uom_id = fields.Many2one("uom.uom", string="UoM", required=True)
    uom_category_id = fields.Many2one(related="product_id.uom_id.category_id")
    product_qty = fields.Float(string="Quantity", default=1.0, required=True, digits="Fuel Qty")
    analytic_account_id = fields.Many2one("account.analytic.account", string="Analytic Account")
    analytic_tag_ids = fields.Many2many("account.analytic.tag", string="Analytic Tags")
    company_id = fields.Many2one(related="agreement_id.company_id", store=True)

    @api.onchange("product_id")
    def _onchange_product_id(self):
        self.product_uom_id = self.product_id.uom_id.id


class TmsAgreementAdvance(models.Model):
    _name = "tms.agreement.advance"
    _description = "Agreement Advance"

    agreement_id = fields.Many2one("tms.agreement", readonly=True, ondelete="cascade", required=True)
    auto_expense = fields.Boolean(
        help="Check this if you want this product and amount to be automatically created when Travel Expense Record is"
        " created."
    )
    product_id = fields.Many2one(
        "product.product", required=True, domain=[("tms_product_category", "=", "real_expense")]
    )
    company_id = fields.Many2one(related="agreement_id.company_id", store=True)
    amount = fields.Monetary(required=True)
    currency_id = fields.Many2one("res.currency", required=True, default=lambda self: self.env.company.currency_id.id)
