# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class FleetVehicleOdometer(models.Model):
    _inherit = ["fleet.vehicle.odometer"]

    last_odometer = fields.Float(string="Last Read")
    distance = fields.Float()
    travel_id = fields.Many2one("tms.travel")
