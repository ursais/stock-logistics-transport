# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Driver(models.Model):
    _inherit = "res.partner"

    # Flags

    is_driver = fields.Boolean(string="Is a driver")
    is_external = fields.Boolean()
    is_training = fields.Boolean()

    # Licences and Certifications

    license_number = fields.Char(string="Driver License Number")
    license_expiry_date = fields.Date()
    other_certifications = fields.Text()

    # Vehicles
    vehicles_ids = fields.Many2many("tms.vehicle", string="Assigned Vehicles")

    # Contact Information

    contact_number = fields.Char()
    emergency_contact_name = fields.Char()
    emergency_contact_number = fields.Char()

    # Personal Information

    date_of_birth = fields.Date()
    gender = fields.Selection(
        [("male", "Male"), ("female", "Female"), ("other", "Other")],
    )
    nationality = fields.Char()
    identity_document = fields.Binary()
    identity_document_type = fields.Char()

    notes = fields.Text(string="Notes/Comments")


class Location(models.Model):
    _inherit = "res.partner"

    location_type = fields.Selection(
        [
            ("train_station", "Train Station"),
            ("airport", "Airport"),
            ("port", "Port"),
            ("bus_station", "Bus Station"),
            ("other", "Other"),
        ],
        default="other",
        required=True,
    )

    # Common Fields for all location types
    code = fields.Char(string="Location Code")
    latitude = fields.Float()
    longitude = fields.Float()

    # Train Station Specific Fields
    station_type = fields.Selection(
        [
            ("metro", "Metro"),
            ("subway", "Subway"),
            ("high_speed", "High-Speed"),
            ("regional", "Regional"),
            ("other_train", "Other Train"),
        ],
        help="Type of train station (e.g., metro, high-speed)",
    )

    # Airport Specific Fields
    has_hangars = fields.Boolean()
    airport_code = fields.Char()
    terminal_capacity = fields.Integer()
    hangar_capacity = fields.Integer()

    # Port Specific Fields
    port_type = fields.Selection(
        [
            ("inland_port", "Inland Port"),
            ("fishing_port", "Fishing Port"),
            ("dry_port", "Dry Port"),
            ("sea_port", "Sea Port"),
            ("river_port", "River Port"),
        ],
        help="Type of port (e.g., sea port, river port)",
    )
    port_code = fields.Char()

    # Bus Station Specific Fields
    bus_station_type = fields.Selection(
        [
            ("city", "City Bus Station"),
            ("intercity", "Intercity Bus Station"),
            ("long_distance", "Long-Distance Bus Station"),
        ],
        help="Type of bus station (e.g., city, intercity)",
    )

    # Additional Fields
    fueling_services = fields.Boolean()
