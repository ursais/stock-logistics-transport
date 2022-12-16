# Copyright 2012, Israel Cruz Argil, Argil Consulting
# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).


from odoo import fields, models


class FleetVehicleLogServices(models.Model):
    _inherit = "fleet.vehicle.log.services"

    validity = fields.Date()
