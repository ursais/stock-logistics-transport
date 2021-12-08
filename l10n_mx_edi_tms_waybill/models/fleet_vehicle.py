# Copyright 2021, Jarsa
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    l10n_mx_edi_trailer_type = fields.Selection(
        selection=[
            ("CTR001", "Easel"),
            ("CTR002", "Box"),
            ("CTR003", "Open box"),
            ("CTR004", "Closed box"),
            ("CTR005", "Pickup Box With Front Loader"),
            ("CTR006", "Refrigerated box"),
            ("CTR007", "Dry box"),
            ("CTR008", "Transfer Box"),
            ("CTR009", "Low Bed or Goose Neck"),
            ("CTR010", "Container chassis"),
            ("CTR011", "Conventional Chassis"),
            ("CTR012", "Special team"),
            ("CTR013", "Stakes"),
            ("CTR014", "Gondola Godmother"),
            ("CTR015", "Industrial Crane"),
            ("CTR016", "Crane"),
            ("CTR017", "Integral"),
            ("CTR018", "Cage"),
            ("CTR019", "Media Redila"),
            ("CTR020", "Pallet or Cells"),
            ("CTR021", "Platform"),
            ("CTR022", "Platform With Crane"),
            ("CTR023", "Curtained Platform"),
            ("CTR024", "Redilas"),
            ("CTR025", "Refrigerator"),
            ("CTR026", "Mixer"),
            ("CTR027", "Half box"),
            ("CTR028", "Tank"),
            ("CTR029", "Hopper"),
            ("CTR031", "Flip"),
            ("CTR032", "Detachable Flip"),
        ],
        string="Trailer Type For Waybill",
    )
