# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).


from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    advance_journal_id = fields.Many2one(
        comodel_name="account.journal",
        domain=[("type", "=", "general")],
    )
    expense_journal_id = fields.Many2one(
        comodel_name="account.journal",
        domain=[("type", "=", "general")],
    )
    driver_license_security_days = fields.Integer(
        help="Number of days to show the expiration date of the driver license",
    )
    insurance_security_days = fields.Integer(
        help="Number of days to show the expiration date of the insurance",
    )
    advance_account_id = fields.Many2one(
        comodel_name="account.account",
        domain=[("reconcile", "=", True)],
    )
    expense_negative_account_id = fields.Many2one(
        comodel_name="account.account",
        domain=[("reconcile", "=", True)],
    )
