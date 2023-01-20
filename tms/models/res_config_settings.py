# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_tms_operating_unit = fields.Boolean(
        string="Operating Unit in TMS"
    )
    module_tms_driver_licence = fields.Boolean(
        string="Driver Licence in TMS"
    )
    module_tms_unit_insurance = fields.Boolean(
        string="Unit Insurance in TMS"
    )
    advance_journal_id = fields.Many2one(
        related="company_id.advance_journal_id", readonly=False
    )
    expense_journal_id = fields.Many2one(
        related="company_id.expense_journal_id", readonly=False
    )
