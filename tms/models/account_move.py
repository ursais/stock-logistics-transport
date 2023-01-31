# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    fuel_id = fields.Many2one("tms.fuel", string="Fuel Log", readonly=True, copy=False)
    waybill_line_id = fields.Many2one("tms.waybill.line", string="Waybill Line", readonly=True, copy=False)
    waybill_id = fields.Many2one(related="waybill_line_id.waybill_id", string="Waybill", store=True)
    expense_line_id = fields.Many2one("tms.expense.line", string="Expense Line", readonly=True, copy=False)

    def _copy_data_extend_business_fields(self, values):
        values.update(
            {
                "fuel_id": self.fuel_id.id,
                "waybill_line_id": self.waybill_line_id.id,
            }
        )
        return super()._copy_data_extend_business_fields(values)
