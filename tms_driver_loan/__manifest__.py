# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "TMS Driver Loans",
    "version": "15.0.1.0.0",
    "category": "Transport",
    "author": "Jarsa",
    "website": "https://www.jarsa.com.mx/page/transport-management-system",
    "depends": [
        "tms",
    ],
    "summary": "Manage Driver Loans",
    "license": "LGPL-3",
    "data": [
        "data/ir_sequence_data.xml",
        "data/product_product_data.xml",
        "views/tms_loan_view.xml",
        "views/res_config_settings_view.xml",
        "views/hr_employee_view.xml",
        "views/tms_expense_view.xml",
        "security/ir.model.access.csv",
    ],
    "demo": [
        "demo/account_account.xml",
        "demo/account_journal.xml",
        "demo/tms_loan.xml",
        "demo/res_company.xml",
    ],
    "installable": True,
}
