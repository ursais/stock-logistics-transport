# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_selection_tms_product_category(self):
        return [
            ("freight", "Freight (Waybill)"),
            ("move", "Moves (Waybill)"),
            ("insurance", "Insurance"),
            ("tolls", "Highway Tolls"),
            ("other", "Other"),
            ("real_expense", "Real Expense"),
            ("made_up_expense", "Made up Expense"),
            ("salary", "Salary"),
            ("salary_retention", "Salary Retention"),
            ("salary_discount", "Salary Discount"),
            ("fuel", "Fuel"),
            ("other_income", "Other Income"),
            ("refund", "Refund"),
            ("negative_balance", "Negative Balance"),
            ("fuel_cash", "Fuel in Cash"),
            ("tollstations", "Tollstations (Expenses)"),
        ]

    tms_product_category = fields.Selection(
        selection=_get_selection_tms_product_category,
        string="TMS Product Category",
    )
    apply_for_salary = fields.Boolean(
        help="Consider this product for salary calculation when the expense is computed if this product is on a "
        "waybill line.",
    )

    @api.constrains("tms_product_category")
    def _check_tms_product_category(self):
        for rec in self:
            categories = {
                "move": _("Moves"),
                "salary": _("Salary"),
                "negative_balance": _("Negative Balance"),
                "indirect_expense": _("Indirect Expense"),
            }
            if rec.tms_product_category in ["move", "salary", "negative_balance", "indirect_expense"]:
                product = rec.search([("tms_product_category", "=", rec.tms_product_category)])
                if len(product) > 1:
                    raise UserError(
                        _(
                            "Only there must be a product with category '%(category)s'",
                            category=categories[rec.tms_product_category],
                        )
                    )
