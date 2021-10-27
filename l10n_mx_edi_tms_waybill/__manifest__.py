# Copyright 2021, Jarsa
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    'name': 'TMS Waybill Complement for Mexico',
    'version': '15.0.1.0.1',
    'category': 'Transport',
    'author': 'Jarsa',
    'website': 'https://www.jarsa.com.mx/page/transport-management-system',
    'depends': [
        'tms',
        'l10n_mx_edi_extended',
    ],
    'summary': 'Add Waybill Complement to TMS',
    'license': 'LGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'data/tms_waybill_template.xml',
        'data/res_country_state_data.xml',
        'views/tms_waybill_view.xml',
        'views/res_partner_view.xml',
        'views/res_country_state_view.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
}
