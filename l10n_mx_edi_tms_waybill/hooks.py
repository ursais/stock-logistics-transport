# Copyright 2021, Jarsa
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from os.path import join, dirname, realpath
import csv

from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    # ==== Load l10n_mx_edi.station ====

    if not env['l10n_mx_edi.station'].search_count([]):
        csv_path = join(dirname(realpath(__file__)), 'data', 'l10n_mx_edi.station.csv')
        station_vals_list = []
        with open(csv_path, 'r') as csv_file:
            for row in csv.DictReader(
                    csv_file,
                    delimiter='|',
                    fieldnames=['l10n_mx_edi_transport_type', 'code', 'name', 'country_xml_id']):
                state = env.ref('base.%s' % row['country_xml_id'], raise_if_not_found=False)
                station_vals_list.append({
                    'l10n_mx_edi_transport_type': row['l10n_mx_edi_transport_type'],
                    'code': row['code'],
                    'name': row['name'],
                    'country_id': state.id if state else False,
                })

        stations = env['l10n_mx_edi.station'].create(station_vals_list)

        if stations:
            cr.execute('''
               INSERT INTO ir_model_data (name, res_id, module, model, noupdate)
                   SELECT 
                        'res_station_' || lower(res_country.code) || '_' || l10n_mx_edi_station.code,
                        l10n_mx_edi_station.id,
                        'l10n_mx_edi_tms_waybill',
                        'l10n_mx_edi.station',
                        TRUE
                   FROM l10n_mx_edi_station
                   JOIN res_country ON res_country.id = l10n_mx_edi_station.country_id
                   WHERE l10n_mx_edi_station.id IN %s
            ''', [tuple(stations.ids)])


def uninstall_hook(cr, registry):
    cr.execute("DELETE FROM ir_model_data WHERE model='l10n_mx_edi.station';")
