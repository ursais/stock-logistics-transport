# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


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
    driver_route_id = fields.Many2one("tms.route")
    customer_route_id = fields.Many2one("tms.route")
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
    notes = fields.Html()
    partner_id = fields.Many2one("res.partner", domain=[("is_company", "=", True)])
    departure_address_id = fields.Many2one(
        "res.partner",
        help="Departure address for current Route and Partner.",
    )
    arrival_address_id = fields.Many2one(
        "res.partner",
        help="Arrival address for current Route and Partner.",
    )

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

    def _get_amount_and_qty(
        self,
        weight=0.0,
        distance=0.0,
        distance_real=0.0,
        qty=0.0,
        volume=0.0,
        income=0.0,
    ):
        if not self:
            raise UserError(_("There is no factor to calculate. Please check the route."))
        factor_list = {
            "weight": weight,
            "distance": distance,
            "distance_real": distance_real,
            "qty": qty,
            "volume": volume,
        }
        amount = 0.0
        quantity = 1.0
        fixed_amount = 0.0
        for rec in self:
            if rec.factor_type == "travel" or rec.mixed:
                fixed_amount = rec.fixed_amount
            elif rec.factor_type == "percent":
                amount = income * (rec.factor / 100)
            else:
                for key, value in factor_list.items():
                    if rec.factor_type == key:
                        if rec.range_start <= value <= rec.range_end:
                            amount = rec.factor
                            quantity = value
                        elif not rec.range_start and not rec.range_end:
                            amount = rec.factor
                            quantity = value
        if not quantity:
            raise UserError(_("Please check if the unit of measure is correct."))
        return {
            "quantity": quantity,
            "amount": amount,
            "fixed_amount": fixed_amount,
        }
