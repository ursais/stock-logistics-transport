# Copyright 2021, Jarsa
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import _, fields, models


class TmsTravel(models.Model):
    _inherit = "tms.travel"

    l10n_mx_edi_configuration = fields.Selection(
        selection=[
            ("VL", "Light cargo vehicle (2 wheels on the front axle and 2 wheels on the rear axle)"),
            ("C2", "Unit Truck (2 wheels on the front axle and 4 wheels on the rear axle)"),
            ("C3", "Unit Truck (2 tires on the front axle and 6 or 8 tires on the two rear axles)"),
            ("C2R2", "Truck-Trailer (6 tires on truck and 8 tires on trailer)"),
            ("C3R2", "Truck-Trailer (10 tires on truck and 8 tires on trailer)"),
            ("C2R3", "Truck-Trailer (6 tires on truck and 12 tires on trailer)"),
            ("C3R3", "Truck-Trailer (10 tires on truck and 12 tires on trailer)"),
            ("T2S1", "Articulated Tractor (6 tires on the tractor, 4 tires on the semi-trailer)"),
            ("T2S2", "Articulated Tractor (6 tires on the tractor, 8 tires on the semi-trailer)"),
            ("T2S3", "Articulated Tractor (6 tires on the tractor, 12 tires on the semi-trailer)"),
            ("T3S1", "Articulated Tractor (10 tires on the tractor, 4 tires on the semi-trailer)"),
            ("T3S2", "Articulated Tractor (10 tires on the tractor, 8 tires on the semi-trailer)"),
            ("T3S3", "Articulated Tractor (10 tires on the tractor, 12 tires on the semi-trailer)"),
            ("T2S1R2", "Tractor Semi-trailer-Trailer (6 tires on the tractor, 4 tires on the semi-trailer and 8 tires on the trailer)"),
            ("T2S2R2", "Tractor Semitrailer-Trailer (6 tires on the tractor, 8 tires on the semi-trailer and 8 tires on the trailer)"),
            ("T2S1R3", "Tractor Truck Semi-Trailer-Trailer (6 tires on the tractor, 4 tires on the semi-trailer and 12 tires on the trailer)"),
            ("T3S1R2", "Tractor Semitrailer-Trailer (10 tires on the tractor, 4 tires on the semi-trailer and 8 tires on the trailer)"),
            ("T3S1R3", "Tractor Semi-trailer-Trailer (10 tires on the tractor, 4 tires on the semi-trailer and 12 tires on the trailer)"),
            ("T3S2R2", "Tractor Semi-trailer-Trailer (10 tires on the tractor, 8 tires on the semi-trailer and 8 tires on the trailer)"),
            ("T3S2R3", "Tractor Semi-trailer-Trailer (10 tires on the tractor, 8 tires on the semi-trailer and 12 tires on the trailer)"),
            ("T3S2R4", "Tractor Semi-trailer-Trailer (10 tires on the tractor, 8 tires on the semi-trailer and 16 tires on the trailer)"),
            ("T2S2S2", "Tractor Semitrailer-Semitrailer (6 tires on the tractor, 8 tires on the front semitrailer and 8 tires on the rear semitrailer)"),
            ("T3S2S2", "Tractor Semi-trailer-Semi-trailer (10 tires on the tractor, 8 tires on the front semi-trailer and 8 tires on the rear semi-trailer)"),
            ("T3S3S2", "Tractor Truck Semitrailer-Semitrailer (10 tires on the tractor, 12 tires on the front semitrailer and 8 tires on the rear semitrailer)"),
            ("OTROEVGP", "Specialized Bulky Cargo and / or Large Weight"),
            ("OTROSG", "Crane Service"),
            ("GPLUTA", "Jib Crane Type A"),
            ("GPLUTB", "Jib Crane Type B"),
            ("GPLUTC", "Type C Jib Crane"),
            ("GPLUTD", "Jib Crane Type D"),
            ("GPLATA", "Type A Platform Crane"),
            ("GPLATB", "Type B Platform Crane"),
            ("GPLATC", "Type C Platform Crane"),
            ("GPLATD", "D Type Platform Crane"),
        ],
        string="Configuration",
    )
