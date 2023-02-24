# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "Agreement for TMS",
    "version": "15.0.1.0.1",
    "category": "Transport",
    "author": "Jarsa",
    "website": "https://www.jarsa.com.mx/page/transport-management-system",
    "depends": [
        "tms",
    ],
    "summary": "Agreement for TMS",
    "license": "LGPL-3",
    "data": [
        "security/ir.model.access.csv",
        "views/tms_agreement_view.xml",
        "wizards/tms_agreement_wizard_view.xml",
        "data/ir_sequence_data.xml",
    ],
    "demo": [
        "demo/tms_agreement.xml",
    ],
}
