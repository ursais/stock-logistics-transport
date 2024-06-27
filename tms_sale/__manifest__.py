# Copyright (C) 2018 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "TMS - Sales",
    "version": "17.0.1.0.0",
    "summary": "Sell transportation management system.",
    "category": "TMS",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-transport",
    "depends": ["tms", "tms_product", "sale_management"],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_order_views.xml",
        "views/tms_order_views.xml",
        "views/product_template_views.xml",
    ],
    "license": "AGPL-3",
    "development_status": "Alpha",
    "maintainers": ["max3903", "santiagordz", "EdgarRetes"],
    "installable": True,
}
