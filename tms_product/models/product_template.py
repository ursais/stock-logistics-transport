# Copyright (C) 2024 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # If it is a vehicle
    tms_vehicle = fields.Boolean(string="Is a Vehicle")
    vehicle_type = fields.Selection(selection="_compute_vehicle_type_selection")
    model_id = fields.Many2one("fleet.vehicle.model", string="Model")

    # If it is a trip
    tms_trip = fields.Boolean(string="Is a Trip")
    tms_tracking = fields.Selection(
        [
            ("no", "Don't create TMS order"),
            ("sale", "Create one TMS order per sale order"),
            ("line", "Create one TMS order per sale order line"),
        ],
        default="no",
        help="""Determines what happens upon sale order confirmation:
                    - None: nothing additional, default behavior.
                    - Per Sale Order: One TMS Order will be created for the sale.
                    - Per Sale Order Line: One TMS Order for each sale order line
                    will be created.""",
    )
    tms_factor_type = fields.Selection(
        [
            ("distance", "Distance"),
            ("weight", "Weight"),
        ],
        default="distance",
        help="""Determines how the trip will be invoiced to the customer:
        - Distance: By the amount of distance traveled
        - Weight: By the amount of weight transported""",
    )
    tms_factor_distance_uom = fields.Many2one(
        "uom.uom",
        domain="[('category_id', '=', 'Length / Distance')]",
        string="Distance Unit of Measure",
    )
    tms_factor_weight_uom = fields.Many2one(
        "uom.uom",
        domain=[("category_id", "=", "Weight")],
        string="Weight Unit of Measure",
    )

    @api.model
    def _compute_vehicle_type_selection(self):
        vehicle_model = self.env["fleet.vehicle.model"]
        vehicle_types = vehicle_model.fields_get(["vehicle_type"])["vehicle_type"][
            "selection"
        ]
        return vehicle_types

    @api.onchange("detailed_type")
    def _onchange_detailed_type(self):
        for product in self:
            if product.detailed_type in ["service"]:
                product.tms_vehicle = False
            else:
                product.tms_trip = False

    @api.onchange("tms_trip")
    def _onchange_tms_trip(self):
        for product in self:
            if not product.tms_trip:
                product.tms_tracking = False
                product.tms_factor_type = False
                product.tms_factor_distance_uom = False
                product.tms_factor_weight_uom = False

    @api.onchange("tms_vehicle")
    def _onchange_tms_vehicle(self):
        for product in self:
            if not product.tms_trip:
                product.vehicle_type = False
                product.model_id = False
