# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models


class TmsExpense(models.Model):
    _name = "tms.expense"
    _inherit = ["tms.expense", "tier.validation"]
    _tier_validation_manual_config = False
