# Copyright 2021, Jarsa
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models


class AccountEdiFormat(models.Model):
    _inherit = "account.edi.format"

    def _l10n_mx_edi_get_invoice_cfdi_values(self, invoice):
        res = super()._l10n_mx_edi_get_invoice_cfdi_values(invoice)
        def _prepare_locations(invoice, type):
            waybill = invoice.waybill_ids
            if type == 'origin':
                partner = waybill.departure_address_id
                location_type = "Origen"
                id = "OR" + str(partner.id).zfill(6)
                date = min(waybill.travel_ids.mapped("date_start"))
                distance = False
            else:
                partner = waybill.arrival_address_id
                location_type = "Destino"
                id = "DE" + str(partner.id).zfill(6)
                date = max(waybill.travel_ids.mapped("date_end"))
                distance = waybill.travel_ids[0].distance_route
            data = {
                "type": location_type,
                "id": id,
                "partner": partner,
                "date": date.strftime('%Y-%m-%dT%H:%M:%S'),
                "distance": distance,
            }
            if waybill.l10n_mx_edi_foreign_country_id:
                data.update({
                    "foreign:": True,
                })
            return data
        travel = invoice.waybill_ids.travel_ids[0]
        res.update({
            "locations": [
                _prepare_locations(invoice, "origin"),
                _prepare_locations(invoice, "destination"),
            ],
            "trailers": travel.trailer1_id + travel.trailer2_id,
        })
        return res
