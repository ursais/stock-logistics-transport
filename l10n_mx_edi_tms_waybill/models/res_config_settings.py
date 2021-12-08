# Copyright 2021, Jarsa
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    l10n_mx_edi_sct_permit_type = fields.Selection(
        related='company_id.l10n_mx_edi_sct_permit_type',
        readonly=False,
        string="SCT Permit Type",
    )
    l10n_mx_edi_sct_permit_number = fields.Char(
        related='company_id.l10n_mx_edi_sct_permit_number',
        readonly=False,
        string="SCT Permit Number",
    )
