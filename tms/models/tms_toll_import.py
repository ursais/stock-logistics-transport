# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class TmsTollImport(models.Model):
    _name = 'tms.toll.import'

    uploaded_file = fields.Binary(string='Upload your file!')
