# Copyright 2012, Israel Cruz Argil, Argil Consulting
# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from __future__ import division

from odoo import api, fields, models


class TmsWaybillLine(models.Model):
    _name = 'tms.waybill.line'
    _description = 'Waybill Line'
    _order = 'sequence, id desc'

    waybill_id = fields.Many2one(
        comodel_name='tms.waybill',
        readonly=True,
        ondelete='cascade',
    )
    name = fields.Char(
        string='Description',
        required=True,
    )
    sequence = fields.Integer(
        help="Gives the sequence order when displaying a list of "
        "waybill lines.",
        default=10,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        required=True,
    )
    unit_price = fields.Float(default=0.0)
    price_subtotal = fields.Float(
        compute='_compute_amount_line',
        string='Subtotal',
    )
    tax_amount = fields.Float(compute='_compute_amount_line')
    tax_ids = fields.Many2many(
        comodel_name='account.tax',
        string='Taxes',
        domain='[("type_tax_use", "=", "sale")]',
    )
    product_qty = fields.Float(
        string='Quantity',
        default=1.0,
    )
    discount = fields.Float(
        string='Discount (%)',
        help="Please use 99.99 format...",
    )
    account_id = fields.Many2one(
        'account.account',
    )

    @api.onchange('product_id')
    def on_change_product_id(self):
        for rec in self:
            fpos = rec.waybill_id.partner_id.property_account_position_id
            fpos_tax_ids = fpos.map_tax(rec.product_id.taxes_id)
            rec.update({
                'account_id': rec.product_id.property_account_income_id.id,
                'tax_ids': fpos_tax_ids,
                'name': rec.product_id.name,
            })

    @api.depends('product_qty', 'unit_price', 'discount')
    def _compute_amount_line(self):
        for rec in self:
            price_discount = (
                rec.unit_price * ((100.00 - rec.discount) / 100))
            taxes = rec.tax_ids.compute_all(
                price_unit=price_discount, currency=rec.waybill_id.currency_id,
                quantity=rec.product_qty, product=rec.product_id,
                partner=rec.waybill_id.partner_id)
            rec.write({
                'price_subtotal': taxes['total_excluded'],
                'tax_amount': taxes['total_included'] - taxes['total_excluded'],
            })
