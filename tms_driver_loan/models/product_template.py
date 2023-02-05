# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_selection_tms_product_category(self):
        res = super()._get_selection_tms_product_category()
        res.append(("loan", "Loan"))
        return res

    tms_product_category = fields.Selection(_get_selection_tms_product_category)
