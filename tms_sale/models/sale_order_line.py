# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    trip_line_ids = fields.One2many("sale.order.line.trip", "order_line_id")

    tms_trip_ticket_id = fields.Many2one("tms.order")
    tms_ticket_ids = fields.One2many("seat.ticket", "sale_line_id")

    tms_order_ids = fields.One2many(
        "tms.order",
        "sale_line_id",
        index=True,
        copy=False,
        help="Transport Order generated by the sales order item",
    )

    tms_factor_uom = fields.Char()
    tms_factor = fields.Float(default=1)

    tms_route_flag = fields.Boolean(string="Use Routes", default=False)
    tms_route_id = fields.Many2one("tms.route", string="Routes")
    tms_origin_id = fields.Many2one(
        "res.partner",
        string="Origin",
        domain="[('tms_location', '=', 'True')]",
        context={"default_tms_location": True},
    )
    tms_destination_id = fields.Many2one(
        "res.partner",
        string="Destination",
        domain="[('tms_location', '=', 'True')]",
        context={"default_tms_location": True},
    )

    tms_scheduled_date_start = fields.Datetime(string="Scheduled Start")
    tms_scheduled_date_end = fields.Datetime(string="Scheduled End")

    has_trip_product = fields.Boolean(readonly=True, default=False)
    seat_ticket = fields.Boolean(readonly=True, default=False)

    def _update_tickets(self, tickets):
        print("\n\n", tickets, "\n\n")
        return True

    @api.constrains(
        "tms_route_flag",
        "tms_route_id",
        "tms_origin_id",
        "tms_destination_id",
        "tms_scheduled_date_start",
        "tms_scheduled_date_end",
    )
    def _check_required_fields(self):
        for record in self:
            if record.trip_line_ids:
                if record.tms_route_flag and not record.tms_route_id:
                    raise ValidationError(
                        _("The route is not set in a trip using predefined routes.")
                    )
                if not record.tms_route_flag:
                    if not record.tms_origin_id:
                        raise ValidationError(
                            _("The origin location from a trip is not set.")
                        )
                    if not record.tms_destination_id:
                        raise ValidationError(
                            _("The destination location from a trip is not set.")
                        )
                if not record.tms_scheduled_date_start:
                    raise ValidationError(
                        _("A scheduled date of start from a trip is not set.")
                    )
                if not record.tms_scheduled_date_end:
                    raise ValidationError(
                        _("A scheduled date of end from a trip is not set.")
                    )

            if (
                record.product_template_id.detailed_type == "service"
                and record.product_template_id.trip_product_type == "seat"
            ):
                if not record.tms_trip_ticket_id:
                    raise ValidationError(_("A ticket isn't assigned to a trip"))

    def _prepare_tms_values(self, **kwargs):
        """
        Prepare the values to create a new TMS Order from a sale order.
        """
        self.ensure_one()
        duration = self.tms_scheduled_date_end - self.tms_scheduled_date_start
        if isinstance(duration, int):
            duration = timedelta(seconds=duration)
        duration_in_s = duration.total_seconds()
        hours = duration_in_s / 3600
        return {
            "sale_id": kwargs.get("so_id", False),
            "sale_line_id": kwargs.get("sol_id", False),
            "company_id": self.company_id.id,
            "route": self.tms_route_flag,
            "route_id": self.tms_route_id.id or None,
            "origin_id": self.tms_origin_id.id or None,
            "destination_id": self.tms_destination_id.id or None,
            "scheduled_date_start": self.tms_scheduled_date_start or None,
            "scheduled_date_end": self.tms_scheduled_date_end or None,
            "scheduled_duration": hours,
        }

    def _prepare_line_tms_values(self, line):
        """
        Prepare the values to create a new TMS Order from a sale order line.
        """
        self.ensure_one()
        vals = self._prepare_tms_values(so_id=self.order_id.id, sol_id=self.id)
        return vals

    def _convert_to_tax_base_line_dict(self, **kwargs):
        """Convert the current record to a dictionary in
        order to use the generic taxes computation method
        defined on account.tax.

        :return: A python dictionary.
        """
        self.ensure_one()
        return self.env["account.tax"]._convert_to_tax_base_line_dict(
            self,
            partner=self.order_id.partner_id,
            currency=self.order_id.currency_id,
            product=self.product_id,
            taxes=self.tax_id,
            price_unit=self.price_unit,
            quantity=self.product_uom_qty * self.tms_factor,
            discount=self.discount,
            price_subtotal=self.price_subtotal,
            **kwargs,
        )

    @api.depends("product_uom_qty", "discount", "price_unit", "tax_id", "tms_factor")
    def _compute_amount(self):
        return super()._compute_amount()

    @api.model
    def write(self, vals):
        line = super().write(vals)
        for trip in self.tms_order_ids:
            if "tms_route_flag" in vals:
                trip.route = vals.get("tms_route_flag")
            if "tms_route_id" in vals:
                trip.route_id = vals.get("tms_route_id")
            if "tms_origin_id" in vals:
                trip.origin_id = vals.get("tms_origin_id")
            if "tms_destination_id" in vals:
                trip.destination_id = vals.get("tms_destination_id")
            if "tms_scheduled_date_start" in vals:
                trip.scheduled_date_start = vals.get("tms_scheduled_date_start")
            if "tms_scheduled_date_end" in vals:
                trip.scheduled_date_end = vals.get("tms_scheduled_date_end")
        return line
