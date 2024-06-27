# Copyright (C) 2024 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import _, fields, models


class TMSOrder(models.Model):
    _name = "tms.order"
    _description = "Transport Management System Order"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # -------------------------------------
    #                  Fields
    # -------------------------------------

    name = fields.Char(
        required=True, index=True, copy=False, default=lambda self: _("New")
    )
    description = fields.Text()
