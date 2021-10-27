# Copyright 2021, Jarsa
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from lxml.objectify import fromstring
from odoo import api, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def l10n_mx_edi_get_cartaporte_etree(self, cfdi):
        """Get the Complement node from the cfdi.
        :param cfdi: The cfdi as etree
        :type cfdi: etree
        :return: the iedu node
        :rtype: etree
        """
        if not hasattr(cfdi, 'Complemento'):
            return None
        attribute = '//cartaporte:CartaPorte'
        namespace = {'cartaporte': 'http://www.sat.gob.mx/CartaPorte'}
        node = cfdi.Complemento.xpath(attribute, namespaces=namespace)
        return node[0] if node else None

    def _l10n_mx_edi_decode_cfdi(self, cfdi_data=None):
        """If the CFDI was signed, try to adds the schemaLocation correctly"""
        result = super()._l10n_mx_edi_decode_cfdi(cfdi_data=cfdi_data)
        if not cfdi_data:
            return result
        cfdi_data = cfdi_data.replace(
            'xmlns__cartaporte', 'xmlns:cartaporte')
        cfdi = fromstring(cfdi_data)
        if 'cartaporte' not in cfdi.nsmap:
            return result
        cfdi.attrib['{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'] = '%s %s %s' % (
            cfdi.get('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'),
            'http://www.sat.gob.mx/CartaPorte',
            'http://www.sat.gob.mx/sitio_internet/cfd/CartaPorte/CartaPorte.xsd'
        )
        result['cfdi_node'] = cfdi
        return result
