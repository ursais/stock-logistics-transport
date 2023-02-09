# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models


class TmsAdvance(models.Model):
    _name = "tms.advance"
    _inherit = ["tms.advance", "tier.validation"]
    _tier_validation_manual_config = False
