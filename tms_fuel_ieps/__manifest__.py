# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "TMS Fuel IEPS",
    "version": "17.0.1.0.1",
    "category": "Transport",
    "author": "Jarsa",
    "website": "https://www.jarsa.com.mx/page/transport-management-system",
    "depends": [
        "tms",
    ],
    "summary": "Manage Fuel IEPS in TMS",
    "license": "LGPL-3",
    "data": [
        "views/tms_fuel_view.xml",
        "views/res_config_settings_view.xml",
        "views/tms_travel_view.xml",
    ],
    "demo": [
        "demo/tms_fuel.xml",
        "demo/res_company.xml",
    ],
    "installable": False,
}
