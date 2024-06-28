# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.TransientModel):
    _inherit = "res.partner"

    name = fields.Char()
    description = fields.Text()
