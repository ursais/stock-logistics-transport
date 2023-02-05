# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    property_tms_loan_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Loan Account",
        company_dependent=True,
        domain=[("reconcile", "=", True)],
        help="Account used to register loans for drivers, "
        "if not set it will take the default account from the company",
    )
