# Copyright 2021, Jarsa
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class ResCountryState(models.Model):
    _inherit = "res.country.state"

    l10n_mx_edi_code = fields.Char(
        string="Code MX",
        help="Country code defined by the SAT in the catalog to "
             "CFDI waybill complement. Will be used in the CFDI "
             "to indicate the state reference."
    )
