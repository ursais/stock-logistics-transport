# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import _, fields, models


class TmsTransportable(models.Model):
    _name = "tms.transportable"
    _description = "Transportable Product"

    name = fields.Char(required=True, translate=True)
    product_uom_id = fields.Many2one("uom.uom", "Unit of Measure ", required=True)
    active = fields.Boolean(default=True)

    def copy(self, default=None):
        default = dict(default or {})
        copied_count = self.search_count([("name", "=like", "Copy of [%(values)s]" % dict(values=self.name))])
        if not copied_count:
            new_name = "Copy of [%(values)s]" % dict(values=self.name)
        else:
            new_name = "Copy of [%(values)s]" % dict(values=", ".join([self.name, str(copied_count)]))

        default["name"] = new_name
        return super().copy(default)

    _sql_constraints = [
        ("name_unique", "UNIQUE(name)", _("Name must be unique")),
    ]
