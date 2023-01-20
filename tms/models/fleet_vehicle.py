# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"
    _order = "economic_number asc, fleet_type asc, license_plate asc"

    fleet_type = fields.Selection(
        [("tractor", "Motorized Unit"), ("trailer", "Trailer"), ("dolly", "Dolly"), ("other", "Other")],
        default="tractor",
        string="Unit Fleet Type",
    )
    economic_number = fields.Char()

    _sql_constraints = [
        (
            "economic_number_company_uniq",
            "unique (economic_number, company_id)",
            "You can not have two vehicles for the same company and economic number",
        ),
    ]

    @api.depends("model_id.brand_id.name", "model_id.name", "license_plate", "economic_number")
    def _compute_vehicle_name(self):
        res = super()._compute_vehicle_name()
        for record in self:
            if record.economic_number:
                record.name = record.economic_number + "/" + record.name
        return res
