# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, fields, models


class TmsExpense(models.Model):
    _inherit = "tms.expense"

    loan_ids = fields.Many2many("tms.loan", string="Loans", readonly=True)
    amount_loan = fields.Monetary(compute="_compute_amounts", store=True)

    @api.depends(
        "expense_line_ids",
        "travel_ids",
        "expense_line_ids.price_unit",
        "expense_line_ids.product_qty",
        "expense_line_ids.tax_ids",
        "expense_line_ids.product_id",
    )
    def _compute_amounts(self):
        for rec in self:
            rec.amount_loan = sum(
                rec.expense_line_ids.filtered(lambda l: l.line_type == "loan").mapped("amount_total")
            )
        return super()._compute_amounts()

    def _get_other_salary_discounts(self):
        res = super()._get_other_salary_discounts()
        res += self.amount_loan
        return res

    def _get_expense_lines(self):
        res = super()._get_expense_lines()
        res.extend(self._get_expense_lines_for_loans())
        return res

    def _get_expense_lines_for_loans(self):
        loans = self.env["tms.loan"].search(
            [("driver_id", "=", self.driver_id.id), ("amount_residual_driver", ">", 0.0), ("state", "=", "confirmed")]
        )
        lines = []
        for loan in loans:
            discount_amount = loan._get_loan_discount_amount(self.date)
            if not discount_amount:
                continue
            lines.append(
                (
                    0,
                    0,
                    {
                        "date": self.date,
                        "name": _("Loan: %(name)s", name=loan.name),
                        "expense_id": self.id,
                        "line_type": "loan",
                        "product_id": loan.product_id.id,
                        "product_qty": 1.0,
                        "price_unit": discount_amount,
                        "control": True,
                        "loan_id": loan.id,
                    },
                )
            )
        return lines

    def _prepare_move_line(self, line=False, invoice=False, line_type=False):
        res = super()._prepare_move_line(line=line, invoice=invoice, line_type=line_type)
        if line and line.line_type == "loan":
            res[0][2].update(
                {
                    "loan_id": line.loan_id.id,
                    "account_id": self.company_id.loan_account_id.id,
                }
            )
        return res

    def action_confirm(self):
        res = super().action_confirm()
        for rec in self:
            rec._reconcile_loans()
        return res

    def _reconcile_loans(self):
        self.ensure_one()
        for line in self.expense_line_ids.filtered(lambda l: l.loan_id):
            move_line = self.move_id.line_ids.filtered(lambda l: l.expense_line_id == line)
            lines_to_reconcile = line.loan_id.move_id.line_ids.filtered(lambda l: l.account_id == move_line.account_id)
            lines_to_reconcile |= move_line
            lines_to_reconcile.reconcile()


class TmsExpenseLine(models.Model):
    _inherit = "tms.expense.line"

    loan_id = fields.Many2one("tms.loan", readonly=True)

    def _get_discount_categories(self):
        res = super()._get_discount_categories()
        res.append("loan")
        return res
