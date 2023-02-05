# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class TmsLoan(models.Model):
    _name = "tms.loan"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "TMS Loan"

    name = fields.Char(readonly=True, copy=False)
    date = fields.Date(required=True, default=fields.Date.context_today)
    date_confirmed = fields.Date(
        string="Confirmed Date",
        readonly=True,
        related="move_id.date",
    )
    driver_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Driver",
        required=True,
        domain=[("driver", "=", True)],
    )
    expense_ids = fields.Many2many("tms.expense", readonly=True, compute="_compute_expense_ids", store=True)
    expense_line_ids = fields.One2many("tms.expense.line", "loan_id", readonly=True)
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("closed", "Closed"),
            ("cancel", "Cancelled"),
        ],
        tracking=True,
        readonly=True,
        default="draft",
    )
    discount_method = fields.Selection(
        selection=[
            ("each", "Each Travel Expense Record"),
            ("weekly", "Weekly"),
            ("fortnightly", "Fortnightly"),
            ("monthly", "Monthly"),
        ],
        required=True,
    )
    discount_type = fields.Selection(
        selection=[
            ("fixed", "Fixed"),
            ("percent", "Loan Percentage"),
        ],
        required=True,
    )
    notes = fields.Html()
    amount = fields.Monetary(required=True)
    discount_factor = fields.Float(required=True)
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
        help="It indicates the payment status of the expense.",
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
    amount_residual = fields.Monetary(compute="_compute_payment_information", store=True)
    amount_residual_driver = fields.Monetary(compute="_compute_payment_information", store=True)
    active = fields.Boolean(default=True)
    product_id = fields.Many2one(
        "product.product", "Discount Product", required=True, domain=[("tms_product_category", "=", "loan")]
    )
    currency_id = fields.Many2one(
        "res.currency", "Currency", required=True, default=lambda self: self.env.user.company_id.currency_id
    )
    move_id = fields.Many2one(
        "account.move",
        "Journal Entry",
        readonly=True,
        help="Link to the automatically generated Journal Items.",
        ondelete="set null",
    )
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.user.company_id)

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
                        and line.partner_id == rec.driver_id.address_home_id
                    ).mapped("amount_residual")
                )
            )
            amount_residual_driver = abs(
                sum(
                    rec.move_id.line_ids.filtered(
                        lambda line: line.account_id.user_type_id.type not in ("receivable", "payable")
                        and line.partner_id == rec.driver_id.address_home_id
                    ).mapped("amount_residual")
                )
            )
            if float_compare(amount_residual, 0.0, precision_rounding=rec.currency_id.rounding) == 0:
                rec.payment_state = "paid"
            elif float_compare(amount_residual, abs(rec.amount), precision_rounding=rec.currency_id.rounding) == 0:
                rec.payment_state = "not_paid"
            else:
                rec.payment_state = "partial"
            related_moves = rec.move_id.line_ids.mapped(
                "matched_debit_ids.debit_move_id.move_id"
            ) | rec.move_id.line_ids.mapped("matched_credit_ids.credit_move_id.move_id")
            rec.update(
                {
                    "payment_move_ids": [(6, 0, related_moves.ids)],
                    "payment_ids": [(6, 0, related_moves.mapped("payment_id").ids)],
                    "amount_residual": amount_residual,
                    "amount_residual_driver": amount_residual_driver,
                }
            )

    @api.depends("expense_line_ids")
    def _compute_expense_ids(self):
        for rec in self:
            rec.expense_ids = rec.expense_line_ids.mapped("expense_id")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = self.env["ir.sequence"].next_by_code("tms.loan") or _("New")
        return super().create(vals_list)

    @api.constrains
    def _check_discount_factor(self):
        for rec in self:
            if rec.discount_type == "percent" and rec.discount_factor > 100.0:
                raise UserError(_("The percentage discount must be less than 100.0"))
            if rec.discount_factor <= 0.0:
                raise UserError(_("The discount factor must be greater than zero"))

    def action_cancel(self):
        for rec in self:
            if rec.payment_state == ["paid", "partial"]:
                raise UserError(_("You can not cancel a loan that has payments"))
            rec.move_id.button_cancel()
            rec.move_id.unlink()
            rec.write(
                {
                    "state": "cancel",
                    "move_id": False,
                }
            )

    def action_confirm(self):
        for rec in self:
            if rec.move_id:
                raise UserError(_("You can not confirm a confirmed loan."))
            move_vals = rec._prepare_loan_move()
            move = self.env["account.move"].create(move_vals)
            move.action_post()
            rec.write(
                {
                    "move_id": move.id,
                    "state": "confirmed",
                }
            )

    def _prepare_loan_move(self):
        self.ensure_one()
        notes = _(
            "<ul>Loan: %(name)s</ul><ul>Driver: %(driver)s</ul>",
            name=self.name,
            driver=self.driver_id.name,
        )
        move_lines = [(0, 0, self._prepare_loan_move_line(nature)) for nature in ["debit", "credit"]]
        return {
            "date": fields.Date.today(),
            "move_type": "entry",
            "company_id": self.company_id.id,
            "journal_id": self._get_loan_journal_id(),
            "ref": _("Loan: %(name)s", name=self.name),
            "line_ids": move_lines,
            "narration": notes,
        }

    def _prepare_loan_move_line(self, nature):
        self.ensure_one()
        total = self.currency_id._convert(self.amount, self.company_id.currency_id, self.company_id, self.date)
        account = self.driver_id.property_tms_loan_account_id.id or self.company_id.loan_account_id.id
        if nature == "credit":
            account = self.driver_id.address_home_id.property_account_payable_id.id
        if not account:
            raise UserError(_("You need to configure the loan account in the Settings of TMS Module."))
        return {
            "name": self.name,
            "partner_id": self.driver_id.address_home_id.id,
            "account_id": account,
            "debit": (total if nature == "debit" else 0.0),
            "credit": (total if nature == "credit" else 0.0),
        }

    def _get_loan_journal_id(self):
        journal_id = self.company_id.loan_journal_id.id
        if not journal_id:
            raise UserError(_("You need to configure the loan journal in the Settins of TMS Module."))
        return journal_id

    def _get_loan_discount_amount(self, date=False):
        self.ensure_one()
        if self.discount_type == "fixed":
            total = self.discount_factor
        elif self.discount_type == "percent":
            total = self.amount * (self.discount_factor / 100)
        if total > self.amount_residual_driver:
            total = self.amount_residual_driver
        if self.discount_method == "each":
            return total
        methods = {
            "monthly": 30,
            "fortnightly": 15,
            "weekly": 7,
        }
        days = methods.get(self.discount_method)
        expense_date = date or fields.Date.context_today(self)
        last_date = max(self.expense_line_ids.mapped("date") + [self.date_confirmed])
        diff_days = (expense_date - last_date).days / days
        if diff_days >= 1:
            return total
        return 0.0

    def action_cancel_draft(self):
        for rec in self:
            rec.state = "draft"

    def unlink(self):
        for rec in self:
            if rec.state in ["confirmed", "closed"]:
                raise UserError(_("You can not delete a Loan in status confirmed or closed"))
            return super().unlink()

    def action_register_payment(self):
        return {
            "name": _("Register Payment"),
            "res_model": "account.payment.register",
            "view_mode": "form",
            "context": {
                "active_model": "tms.loan",
                "active_ids": self.ids,
                "dont_redirect_to_payments": True,
            },
            "target": "new",
            "type": "ir.actions.act_window",
        }

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
