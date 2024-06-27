# Copyright (C) 2024 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class TMSRoute(models.Model):
    _name = "tms.route"
    _description = "Transport Management System Route"

    # -------------------------------------
    #                  Fields
    # -------------------------------------

    name = fields.Char(required=True)
    description = fields.Text()
