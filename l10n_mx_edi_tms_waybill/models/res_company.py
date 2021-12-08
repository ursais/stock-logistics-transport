# Copyright 2021, Jarsa
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from lxml import etree

from odoo import api, fields, models

class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_mx_edi_sct_permit_type = fields.Selection(
        selection=[
            ("TPAF01", "Federal motor transport of general cargo."),
            ("TPAF02", "Private cargo transportation."),
            ("TPAF03", "Federal Autotransport of Specialized Cargo of hazardous materials and waste."),
            ("TPAF04", "Transportation of cars without rolling in a gondola-type vehicle."),
            ("TPAF05", "Transportation of heavy weight and / or volume cargo up to 90 tons."),
            ("TPAF06", "Transportation of specialized cargo of great weight and / or volume of more than 90 tons."),
            ("TPAF07", "Private transportation of hazardous materials and waste."),
            ("TPAF08", "International long-haul freight motor transport."),
            ("TPAF09", "International motor transport of specialized cargo of long-haul hazardous materials and waste."),
            ("TPAF10", "Federal Motor Carrier of General Cargo whose scope of application includes the border with the United States."),
            ("TPAF11", "Federal Motor Carrier of Specialized Cargo whose scope of application includes the border strip with the United States."),
            ("TPAF12", "Auxiliary service of dragging in the general communication routes."),
            ("TPAF13", "Auxiliary service of towing, hauling and salvage services, and vehicle storage in general communication routes."),
            ("TPAF14", "Parcel and courier service in general communication channels."),
            ("TPAF15", "Special transport for the transit of industrial cranes with a maximum weight of 90 tons."),
            ("TPAF16", "Federal service for leasing companies federal public service."),
            ("TPAF17", "New vehicle transfer companies."),
            ("TPAF18", "Manufacturers or distributors of new vehicles."),
            ("TPAF19", "Express authorization to circulate on the roads and bridges of federal jurisdiction with double-articulated tractor-trailer configurations."),
            ("TPAF20", "Federal Autotransport of Specialized Cargo of funds and securities."),
            ("TPTM01", "Temporary permit for cabotage navigation"),
            ("TPTA01", "Concession and / or authorization for regular national and / or international service for Mexican companies"),
            ("TPTA02", "Permit for regular air service of foreign companies"),
            ("TPTA03", "Permit for non-regular national and international charter service"),
            ("TPTA04", "Permit for non-regular national and international air taxi service"),
            ("TPXX00", "Permission not contemplated in the catalog."),
        ],
        string="SCT Permit Type",
    )
    l10n_mx_edi_sct_permit_number = fields.Char(
        string="SCT Permit Number",
    )

    @api.model
    def _load_xsd_complements(self, content):
        content = super()._load_xsd_complements(content)
        complements = [
            ["http://www.sat.gob.mx/CartaPorte20",
             "http://www.sat.gob.mx/sitio_internet/cfd/CartaPorte/CartaPorte20.xsd"],
        ]
        for complement in complements:
            xsd = {'namespace': complement[0], 'schemaLocation': complement[1]}
            node = etree.Element('{http://www.w3.org/2001/XMLSchema}import', xsd)
            content.insert(0, node)
        return content
