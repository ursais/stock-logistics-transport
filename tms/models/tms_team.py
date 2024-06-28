# Copyright (C) 2024 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class TMSTeam(models.Model):
    _name = "tms.team"
    _description = "Transport Management System Team"
    # _inherit = ["mail.thread", "mail.activity.mixin"]

    # -------------------------------------
    #                  Fields
    # -------------------------------------

    name = fields.Char(required=True)
    description = fields.Text()
