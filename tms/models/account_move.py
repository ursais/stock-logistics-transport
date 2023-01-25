# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    # waybill_ids = fields.One2many("tms.waybill", "invoice_id", string="Waybills", readonly=True)

    # def button_cancel(self):
    #     for rec in self:
    #         advances = self.env["tms.advance"].search([("payment_move_id", "=", rec.id)])
    #         expenses = self.env["tms.expense"].search([("payment_move_id", "=", rec.id)])
    #         loans = self.env["tms.expense.loan"].search([("payment_move_id", "=", rec.id)])
    #         if advances:
    #             advances.write(
    #                 {
    #                     "paid": False,
    #                 }
    #             )
    #         if expenses:
    #             expenses.write(
    #                 {
    #                     "paid": False,
    #                 }
    #             )
    #         if loans:
    #             loans.write(
    #                 {
    #                     "paid": False,
    #                 }
    #             )
    #     return super().button_cancel()


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    fuel_id = fields.Many2one("tms.fuel", string="Fuel Log", readonly=True, copy=False)

    def _copy_data_extend_business_fields(self, values):
        values["fuel_id"] = self.fuel_id.id
        return super()._copy_data_extend_business_fields(values)
