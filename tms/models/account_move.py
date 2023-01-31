# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    waybill_id = fields.Many2one("tms.waybill", compute="_compute_waybill_id", store=True)

    @api.depends("line_ids.waybill_id")
    def _compute_waybill_id(self):
        for rec in self:
            if rec.line_ids and rec.line_ids[0].waybill_id:
                rec.waybill_id = rec.line_ids.waybill_id


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    fuel_id = fields.Many2one("tms.fuel", string="Fuel Log", readonly=True, copy=False)
    waybill_line_id = fields.Many2one("tms.waybill.line", string="Waybill Line", readonly=True, copy=False)
    waybill_id = fields.Many2one(related="waybill_line_id.waybill_id", string="Waybill", store=True)
    expense_line_id = fields.Many2one("tms.expense.line", string="Expense Line", readonly=True, copy=False)
