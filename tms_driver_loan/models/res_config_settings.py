# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    loan_account_id = fields.Many2one(
        related="company_id.loan_account_id",
        readonly=False,
    )
    loan_journal_id = fields.Many2one(
        related="company_id.loan_journal_id",
        readonly=False,
    )
