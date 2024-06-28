# Copyright (C) 2024 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class TMSVehicle(models.Model):
    _name = "tms.vehicle"
    _description = "Transport Management System Vehicle"

    # General Information

    name = fields.Char(string="Vehicle Name", required=True)
    vehicle_type = fields.Selection(
        [
            ("truck", "Truck"),
            ("car", "Car"),
            ("van", "Van"),
            ("train", "Train"),
            ("boat", "Boat"),
            ("plane", "Plane"),
            ("other", "Other"),
        ],
        required=True,
    )
    license_plate = fields.Char()
    manufacturer = fields.Char()
    model = fields.Char()
    year_manufacture = fields.Integer(string="Year of Manufacture")

    # Fuel & Engine

    fuel_type = fields.Char()
    fuel_efficiency = fields.Char()
    transmission_type = fields.Char()
    engine_size = fields.Char()
    horsepower = fields.Char()

    # Capacity

    seating_capacity = fields.Integer()
    max_payload_capacity = fields.Float(string="Maximum Payload Capacity")
    max_towing_capacity = fields.Float(string="Maximum Towing Capacity")

    # Dimensions

    length = fields.Float()
    width = fields.Float()
    height = fields.Float()
    gross_vehicle_weight = fields.Float()

    # Insurance

    vehicle_class = fields.Char()
    insurance_policy_number = fields.Char()
    insurance_company = fields.Char()
    insurance_validity_from = fields.Date()
    insurance_validity_to = fields.Date(string="Insurance Valid To")
    registration_date = fields.Date()
    registration_expiry_date = fields.Date()
    registration_authority = fields.Char()

    # Value

    owner_id = fields.Many2one("res.partner", string="Owner")
    purchase_date = fields.Date()
    purchase_price = fields.Float()
    depreciation_schedule = fields.Selection(
        [("linear", "Linear"), ("degressive", "Degressive")],
    )
    current_value = fields.Float()

    # Location

    location_latitude = fields.Float()
    location_longitude = fields.Float()

    # Service

    current_mileage = fields.Float()
    last_service_date = fields.Date()
    next_service_date = fields.Date()
    service_history = fields.Text()
    maintenance_schedule = fields.Text()
    warranty_details = fields.Text()

    # Driver
    current_driver_id = fields.Many2one("res.partner", string="Current Driver")

    # Status
    operational_status = fields.Selection(
        [
            ("active", "Active"),
            ("maintenance", "In Maintenance"),
            ("out_of_service", "Out of Service"),
        ],
        default="active",
    )

    # Routes
    assigned_routes = fields.Many2many("tms.route")
