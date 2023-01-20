# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class FleetVehicleEngine(models.Model):
    _name = "fleet.vehicle.engine"
    _description = "Engines of Vehicles"

    name = fields.Char(required=True)
