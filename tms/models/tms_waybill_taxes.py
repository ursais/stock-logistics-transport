# Copyright 2012, Israel Cruz Argil, Argil Consulting
# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class TmsWaybillTaxes(models.Model):
    _name = "tms.waybill.taxes"
    _description = "Waybill Taxes"
    _order = "tax_amount desc"

    waybill_id = fields.Many2one(
        comodel_name='tms.waybill',
        string='Waybill',
        readonly=True,
        required=True,
    )
    tax_id = fields.Many2one(
        comodel_name='account.tax',
        string='Tax',
        readonly=True,
        required=True,
    )
    account_id = fields.Many2one(
        comodel_name='account.account',
        string='Tax Account',
    )
    account_analytic_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic account',
    )
    tax_amount = fields.Float(
        digits='Account',
        readonly=True
    )
