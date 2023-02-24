# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class TmsAdvance(models.Model):
    _inherit = "tms.advance"

    agreement_id = fields.Many2one("tms.agreement", readonly=True, copy=False)
