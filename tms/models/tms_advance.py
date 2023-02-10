# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class TmsAdvance(models.Model):
    _name = "tms.advance"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Money advance payments for Travel expenses"
    _order = "name desc, date desc"

    name = fields.Char(string="Advance Number", readonly=True, default="/", copy=False)
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("done", "Done"),
            ("closed", "Closed"),
            ("cancel", "Cancelled"),
        ],
        tracking=True,
        readonly=True,
        default="draft",
    )
    date = fields.Date(required=True, default=fields.Date.context_today)
    travel_id = fields.Many2one("tms.travel", required=True, ondelete="restrict")
    unit_id = fields.Many2one(
        "fleet.vehicle",
        related="travel_id.unit_id",
        store=True,
    )
    driver_id = fields.Many2one(
        "hr.employee",
        related="travel_id.driver_id",
        string="Driver",
        store=True,
    )
    amount = fields.Monetary(required=True)
    amount_residual = fields.Monetary(
        compute="_compute_payment_information",
        store=True,
    )
    notes = fields.Html()
    move_id = fields.Many2one(
        "account.move",
        "Journal Entry",
        help="Link to the automatically generated Journal Items.",
        readonly=True,
        ondelete="restrict",
        copy=False,
    )
    payment_state = fields.Selection(
        [
            ("not_paid", "Not Paid"),
            ("paid", "Paid"),
            ("partial", "Partially Paid"),
        ],
        readonly=True,
        compute="_compute_payment_information",
        store=True,
        tracking=True,
        help="It indicates the payment status of the advance.",
    )
    payment_move_ids = fields.Many2many(
        "account.move",
        string="Payment Entries",
        readonly=True,
        compute="_compute_payment_information",
        store=True,
    )
    payment_ids = fields.Many2many(
        "account.payment",
        readonly=True,
        compute="_compute_payment_information",
        store=True,
    )
    currency_id = fields.Many2one(
        "res.currency", required=True, default=lambda self: self.env.user.company_id.currency_id
    )
    auto_expense = fields.Boolean(
        help="Check this if you want this product and amount to be "
        "automatically created when Travel Expense Record is created."
    )
    expense_id = fields.Many2one("tms.expense", readonly=True, copy=False)
    product_id = fields.Many2one(
        "product.product", required=True, domain=[("tms_product_category", "=", "real_expense")]
    )
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.user.company_id)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = self.env["ir.sequence"].next_by_code("tms.advance") or _("New")
        return super().create(vals_list)

    @api.constrains("amount")
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise UserError(_("The amount must be greater than zero."))

    @api.depends(
        "move_id.line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched",
        "move_id.line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual",
        "move_id.line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency",
        "move_id.line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched",
        "move_id.line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual",
        "move_id.line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency",
        "move_id.line_ids.debit",
        "move_id.line_ids.credit",
        "move_id.line_ids.currency_id",
        "move_id.line_ids.amount_currency",
        "move_id.line_ids.amount_residual",
        "move_id.line_ids.amount_residual_currency",
        "move_id.line_ids.payment_id.state",
        "move_id.line_ids.full_reconcile_id",
    )
    def _compute_payment_information(self):
        for rec in self:
            if not rec.move_id:
                rec.payment_state = False
                continue
            amount_residual = abs(
                sum(
                    rec.move_id.line_ids.filtered(
                        lambda line: line.account_id.user_type_id.type in ("receivable", "payable")
                    ).mapped("amount_residual")
                )
            )
            if float_compare(amount_residual, 0.0, precision_rounding=rec.currency_id.rounding) == 0:
                rec.payment_state = "paid"
            elif float_compare(amount_residual, rec.amount, precision_rounding=rec.currency_id.rounding) == 0:
                rec.payment_state = "not_paid"
            else:
                rec.payment_state = "partial"
            related_moves = rec.move_id.line_ids.mapped(
                "matched_debit_ids.debit_move_id.move_id"
            ) | rec.move_id.line_ids.mapped("matched_credit_ids.credit_move_id.move_id")
            rec.payment_move_ids = related_moves
            rec.payment_ids = related_moves.mapped("payment_id")
            rec.amount_residual = amount_residual

    def action_confirm(self):
        for rec in self:
            if rec.move_id:
                raise UserError(_("You can not confirm a confirmed advance."))
            move_vals = rec._prepare_advance_move()
            move = self.env["account.move"].create(move_vals)
            move.action_post()
            rec.write(
                {
                    "move_id": move.id,
                    "state": "confirmed",
                }
            )

    def _prepare_advance_move(self):
        self.ensure_one()
        notes = _(
            "<ul>Advance: %(name)s</ul><ul>Travel: %(travel)s</ul><ul>Driver: %(driver)s</ul>"
            "<ul>Vehicle: %(vehicle)s</ul>",
            name=self.name,
            travel=self.travel_id.name,
            driver=self.driver_id.name,
            vehicle=self.unit_id.name,
        )
        move_lines = [(0, 0, self._prepare_advance_move_line(nature)) for nature in ["debit", "credit"]]
        return {
            "date": fields.Date.today(),
            "move_type": "entry",
            "company_id": self.company_id.id,
            "journal_id": self._get_advance_journal_id(),
            "ref": _("Advance: %(name)s", name=self.name),
            "line_ids": move_lines,
            "narration": notes,
        }

    def _prepare_advance_move_line(self, nature):
        self.ensure_one()
        total = self.currency_id._convert(self.amount, self.company_id.currency_id, self.company_id, self.date)
        account = self.driver_id.property_tms_advance_account_id.id or self.company_id.advance_account_id.id
        if nature == "credit":
            account = self.driver_id.address_home_id.property_account_payable_id.id
        if not account and nature == "debit":
            raise UserError(_("You need to configure the advance account in the Settings of TMS Module."))
        if not account and nature == "credit":
            raise UserError(_("You need to configure the payable account in the partner."))
        return {
            "name": self.name,
            "partner_id": self.driver_id.address_home_id.id,
            "account_id": account,
            "debit": (total if nature == "debit" else 0.0),
            "credit": (total if nature == "credit" else 0.0),
        }

    def _get_advance_journal_id(self):
        journal_id = self.company_id.advance_journal_id.id
        if not journal_id:
            raise UserError(_("You need to configure the advance journal in the Settins of TMS Module."))
        return journal_id

    def action_cancel(self):
        for rec in self:
            if rec.payment_state in ["in_payment", "paid", "partial"]:
                raise UserError(
                    _(
                        "Could not cancel this advance because"
                        " the advance is already paid. "
                        "Please cancel the payment first."
                    )
                )
            rec.move_id.button_cancel()
            rec.write(
                {
                    "state": "cancel",
                    "move_id": False,
                }
            )

    def action_cancel_draft(self):
        for rec in self:
            if rec.travel_id.state == "cancel":
                raise UserError(_("Could not set this advance to draft because the travel is cancelled."))
            rec.state = "draft"

    def action_register_payment(self):
        if any(advance.payment_state == "paid" for advance in self):
            raise UserError(_("At least one of the selected advances is already paid."))
        return {
            "name": _("Register Payment"),
            "res_model": "account.payment.register",
            "view_mode": "form",
            "context": {
                "active_model": "tms.advance",
                "active_ids": self.ids,
                "dont_redirect_to_payments": True,
            },
            "target": "new",
            "type": "ir.actions.act_window",
        }

    def action_open_payments(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_account_payments_payable")
        if len(self.payment_ids) > 1:
            action["domain"] = [("id", "in", self.payment_ids.ids)]
        elif len(self.payment_ids) == 1:
            form_view = [(self.env.ref("account.view_account_payment_form").id, "form")]
            if "views" in action:
                action["views"] = form_view + [(state, view) for state, view in action["views"] if view != "form"]
            else:
                action["views"] = form_view
            action["res_id"] = self.payment_ids.id
        else:
            action = {"type": "ir.actions.act_window_close"}

        action["context"] = {
            "no_create": True,
            "no_edit": True,
        }
        return action

    def action_open_related_moves(self):
        self.ensure_one()
        moves = self.payment_move_ids | self.move_id
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_journal_line")
        if len(moves) > 1:
            action["domain"] = [("id", "in", moves.ids)]
        elif len(moves) == 1:
            form_view = [(self.env.ref("account.view_move_form").id, "form")]
            if "views" in action:
                action["views"] = form_view + [(state, view) for state, view in action["views"] if view != "form"]
            else:
                action["views"] = form_view
            action["res_id"] = moves.id
        else:
            action = {"type": "ir.actions.act_window_close"}

        action["context"] = {
            "no_create": True,
            "no_edit": True,
        }
        return action
