# Copyright (C) 2024 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class TMSStage(models.Model):
    _name = "tms.stage"
    _description = "Transport Management System Stage"

    # -------------------------------------
    #                  Fields
    # -------------------------------------

    name = fields.Char(required=True)
    description = fields.Text()
