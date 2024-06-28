# Copyright (C) 2024 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class TMSRoute(models.Model):
    _name = "tms.route"
    _description = "Transport Management System Route"

    # -------------------------------------
    #                  Fields
    # -------------------------------------

    name = fields.Char(string="Route Name", required=True)
    origin_location_id = fields.Many2one(
        "res.partner",
        string="Origin Location",
        domain="[('location_type', 'in', ['train_station', 'airport', 'port', 'bus_station'])]",
        required=True,
    )
    destination_location_id = fields.Many2one(
        "res.partner",
        string="Destination Location",
        domain="[('location_type', 'in', ['train_station', 'airport', 'port', 'bus_station'])]",
        required=True,
    )
    stop_location_ids = fields.Many2many(
        "res.partner",
        string="Stop Locations",
        domain="[('location_type', 'in', ['train_station', 'airport', 'port', 'bus_station'])]",
    )
    vehicle_id = fields.Many2one("tms.vehicle", string="Vehicle", required=True)

    # Route Details
    distance = fields.Float(string="Distance (km)")
    estimated_time = fields.Float()
    estimated_time_uom = fields.Selection([("days", "Days"), ("hours", "Hours")])
    fuel_needed = fields.Float(string="Fuel Needed (liters)")

    # Costs and Pricing
    toll_cost = fields.Float(string="Total Toll Cost")
    maintenance_cost = fields.Float()
    other_costs = fields.Float()
    total_cost = fields.Float(compute="_compute_total_cost", store=True)

    # Constraints and Optimization
    max_weight = fields.Float(string="Maximum Weight (kg)")
    max_volume = fields.Float(string="Maximum Volume (m³)")
    min_fuel_efficiency = fields.Float(string="Minimum Fuel Efficiency")

    # Notes and Comments
    notes = fields.Text(string="Notes/Comments")

    # Compute Methods
    @api.depends("toll_cost", "maintenance_cost", "other_costs")
    def _compute_total_cost(self):
        for route in self:
            route.total_cost = (
                route.toll_cost + route.maintenance_cost + route.other_costs
            )
