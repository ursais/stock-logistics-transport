# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    ieps_account_id = fields.Many2one(
        "account.account",
        string="IEPS Account",
        help="Account used to record the IEPS tax",
    )
