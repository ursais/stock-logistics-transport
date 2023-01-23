# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    @api.model
    def default_get(self, fields_list):
        active_model = self._context.get("active_model")
        if active_model in self._get_tms_models_for_payment():
            records = self.env[active_model].browse(self._context.get("active_ids"))
            context = {
                "active_model": "account.move",
                "active_ids": records.mapped("move_id").ids,
            }
        return super(AccountPaymentRegister, self.with_context(**context)).default_get(
            fields_list
        )  # pylint: disable=super-with-arguments

    def _get_tms_models_for_payment(self):
        return ["tms.advance", "tms.expense"]

    def _create_payments(self):
        active_model = self._context.get("active_model")
        if active_model in self._get_tms_models_for_payment():
            records = self.env[active_model].browse(self._context.get("active_ids"))
            context = {
                "active_model": "account.move",
                "active_ids": records.mapped("move_id").ids,
            }
        return super(
            AccountPaymentRegister, self.with_context(**context)
        )._create_payments()  # pylint: disable=super-with-arguments
