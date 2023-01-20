# Copyright 2017, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    tms_type = fields.Selection(
        [
            ("advance", "Advance"),
            ("expense", "Expense"),
        ],
        string="TMS Type",
        help="Used to define if this journal is used for advances or expenses",
    )

    _sql_constraints = [
        (
            "tms_type_company_uniq",
            "unique (tms_type, company_id)",
            "You can not have two journals for the same company and TMS Type",
        ),
    ]
