# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from __future__ import division

from odoo import _, api, fields, models


class TmsFactor(models.Model):
    _name = "tms.factor"
    _description = "Factors to calculate Payment (Driver/Supplier) & Client charge"
    _order = "sequence"

    def _get_category_selection(self):
        return [
            ("driver", "Driver"),
            ("customer", "Customer"),
        ]

    def _get_factor_type_selection(self):
        return [
            ("distance", "Distance Route (Km/Mi)"),
            ("distance_real", "Distance Real (Km/Mi)"),
            ("weight", "Weight"),
            ("travel", "Travel"),
            ("qty", "Quantity"),
            ("volume", "Volume"),
            ("percent", "Income Percent"),
        ]

    name = fields.Char(required=True)
    route_id = fields.Many2one("tms.route", string="Route")
    category = fields.Selection(_get_category_selection, required=True)
    factor_type = fields.Selection(
        _get_factor_type_selection,
        required=True,
        help="For next options you have to type Ranges or Fixed Amount\n - "
        "Distance Route (Km/mi)\n - Distance Real (Km/Mi)\n - Weight\n"
        " - Quantity\n - Volume\nFor next option you only have to type"
        " Fixed Amount:\n - Travel\nFor next option you only have to type"
        " Factor like 10.5 for 10.50%:\n - Income Percent",
    )
    range_start = fields.Float()
    range_end = fields.Float()
    factor = fields.Float()
    fixed_amount = fields.Float()
    mixed = fields.Boolean()
    sequence = fields.Integer(help="Gives the sequence calculation for these factors.", default=10)
    notes = fields.Text()

    @api.onchange("factor_type")
    def _onchange_factor_type(self):
        values = {
            "distance": _("Distance Route (Km/Mi)"),
            "distance_real": _("Distance Real (Km/Mi)"),
            "weight": _("Weight"),
            "travel": _("Travel"),
            "qty": _("Quantity"),
            "volume": _("Volume"),
            "percent": _("Income Percent"),
        }
        self.name = values.get(self.factor_type)

    def _get_amount(
        self, weight=0.0, distance=0.0, distance_real=0.0, qty=0.0, volume=0.0, income=0.0, employee=False
    ):
        factor_list = {
            "weight": weight,
            "distance": distance,
            "distance_real": distance_real,
            "qty": qty,
            "volume": volume,
        }
        amount = 0.0
        for rec in self:
            if rec.factor_type == "travel":
                amount += rec.fixed_amount
            elif rec.factor_type == "percent":
                amount += income * (rec.factor / 100)
            else:
                for key, value in factor_list.items():
                    if rec.factor_type == key:
                        if rec.range_start <= value <= rec.range_end:
                            amount += rec.factor * value
                        elif not rec.range_start and not rec.range_end:
                            amount += rec.factor * value
                # TODO: Add validation to check if values are in range
            if rec.mixed and rec.factor_type != "travel":
                amount += rec.fixed_amount
        return amount
