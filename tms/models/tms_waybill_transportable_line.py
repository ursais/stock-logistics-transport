# Copyright 2012, Israel Cruz Argil, Argil Consulting
# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class TmsWaybillTransportableLine(models.Model):
    _name = 'tms.waybill.transportable.line'
    _description = 'Shipped Product'
    _order = 'sequence, id desc'

    transportable_id = fields.Many2one(
        comodel_name='tms.transportable',
        required=True,
    )
    name = fields.Char(
        string='Description',
        required=True,
    )
    transportable_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Unit of Measure ',
        required=True,
    )
    quantity = fields.Float(
        string='Quantity (UoM)',
        required=True,
        default=0.0,
    )
    notes = fields.Char()
    waybill_id = fields.Many2one(
        comodel_name='tms.waybill',
        required=True,
        ondelete='cascade',
        readonly=True,
    )
    sequence = fields.Integer(
        help="Gives the sequence order when displaying a list of"
        " sales order lines.", default=10)

    @api.onchange('transportable_id')
    def _onchange_transportable_id(self):
        self.update({
            'name': self.transportable_id.name,
            'transportable_uom_id': self.transportable_id.uom_id.id,
        })
