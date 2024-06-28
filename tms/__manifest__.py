# Copyright (C) 2018 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Transportation Management System",
    "summary": "Manage Vehicles, Routes and Delivers",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    "category": "Transportation Management System",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-transport",
    "depends": ["base"],
    "data": [
        "security/res_groups.xml",
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "views/res_config_settings.xml",
        "views/res_partner.xml",
        "views/tms_order.xml",
        "views/tms_stage.xml",
        "views/tms_team.xml",
        "views/tms_vehicle.xml",
        "views/menu.xml",
    ],
    "demo": [],
    "application": True,
    "development_status": "Alpha",
    "maintainers": ["max3903", "santiagordz"],
    "assets": {},
}
