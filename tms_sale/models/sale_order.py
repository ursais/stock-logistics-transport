# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from markupsafe import Markup

from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    tms_order_ids = fields.Many2many(
        "tms.order",
        compute="_compute_tms_order_ids",
        string="Transport orders associated to this sale",
    )
    tms_order_count = fields.Integer(
        string="Transport Orders", compute="_compute_tms_order_ids"
    )

    has_tms_order = fields.Boolean(compute="_compute_has_tms_order")

    tms_route_flag = fields.Boolean(string="Use Routes")
    tms_route_id = fields.Many2one("tms.route", string="Routes")
    tms_origin_id = fields.Many2one(
        "res.partner",
        string="Origin",
        domain="[('tms_type', '=', 'location')]",
        context={"default_tms_type": "location"},
    )
    tms_destination_id = fields.Many2one(
        "res.partner",
        string="Destination",
        domain="[('tms_type', '=', 'location')]",
        context={"default_tms_type": "location"},
    )

    tms_scheduled_date_start = fields.Datetime(string="Scheduled Start")
    tms_scheduled_date_end = fields.Datetime(string="Scheduled End")

    @api.depends("order_line")
    def _compute_has_tms_order(self):
        for sale in self:
            has_tms_order = any(
                line.product_template_id.tms_trip for line in sale.order_line
            )
            sale.has_tms_order = has_tms_order

    @api.depends("order_line")
    def _compute_tms_order_ids(self):
        for sale in self:
            tms = self.env["tms.order"].search(
                [
                    "|",
                    ("sale_id", "=", sale.id),
                    ("sale_line_id", "in", sale.order_line.ids),
                ]
            )
            sale.tms_order_ids = tms
            sale.tms_order_count = len(sale.tms_order_ids)

    def _prepare_line_tms_values(self, line):
        """
        Prepare the values to create a new TMS Order from a sale order line.
        """
        self.ensure_one()
        vals = self._prepare_tms_values(so_id=self.id, sol_id=line.id)
        return vals

    def _prepare_tms_values(self, **kwargs):
        """
        Prepare the values to create a new TMS Order from a sale order.
        """
        self.ensure_one()
        duration = self.tms_scheduled_date_end - self.tms_scheduled_date_start
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

    def _tms_generate_sale_tms_orders(self, new_tms_sol):
        """
        Generate the TMS Order for this sale order if it doesn't exist.
        """
        self.ensure_one()
        new_tms_orders = self.env["tms.order"]

        if new_tms_sol:
            tms_by_sale = self.env["tms.order"].search(
                [("sale_id", "=", self.id), ("sale_line_id", "=", False)]
            )
            if not tms_by_sale:
                vals = self._prepare_tms_values(so_id=self.id)
                tms_by_sale = self.env["tms.order"].sudo().create(vals)
                new_tms_orders |= tms_by_sale
            new_tms_sol.write({"tms_order_id": tms_by_sale.id})

        return new_tms_orders

    def _tms_generate_line_tms_orders(self, new_tms_sol):
        """
        Generate TMS Orders for the given sale order lines.

        Override this method to filter lines to generate TMS Orders for.
        """
        self.ensure_one()
        new_tms_orders = self.env["tms.order"]

        for line in new_tms_sol:
            vals = self._prepare_line_tms_values(line)
            tms_by_line = self.env["tms.order"].sudo().create(vals)
            line.write({"tms_order_id": tms_by_line.id})
            new_tms_orders |= tms_by_line

        return new_tms_orders

    def _tms_generate(self):
        """
        Generate TMS Orders for this sale order.

        Override this method to add new tms_tracking types.
        """
        self.ensure_one()
        new_tms_orders = self.env["tms.order"]

        # Process lines set to TMS Sale
        new_tms_sale_sol = self.order_line.filtered(
            lambda L: L.product_id.tms_tracking == "sale" and not L.tms_order_id
        )
        new_tms_orders |= self._tms_generate_sale_tms_orders(new_tms_sale_sol)

        # Create new FSM Order for lines set to FSM Line
        new_tms_line_sol = self.order_line.filtered(
            lambda L: L.product_id.tms_tracking == "line" and not L.tms_order_id
        )

        new_tms_orders |= self._tms_generate_line_tms_orders(new_tms_line_sol)

        return new_tms_orders

    def _tms_generation(self):
        """
        Create TMS Orders based on the products' configuration.
        :rtype: list(TMS Orders)
        :return: list of newly created TMS Orders
        """
        created_tms_orders = self.env["tms.order"]

        for sale in self:
            new_tms_orders = self._tms_generate()

            if len(new_tms_orders) > 0:
                created_tms_orders |= new_tms_orders
                # If FSM Orders were created, post a message to the Sale Order
                sale._post_tms_message(new_tms_orders)

        return created_tms_orders

    def _post_tms_message(self, tms_orders):
        """
        Post messages to the Sale Order and the newly created TMS Orders
        """
        self.ensure_one()
        for tms_order in tms_orders:
            tms_order.message_mail_with_source(
                "mail.message_origin_link",
                render_values={"self": tms_order, "origin": self},
                subtype_id=self.env.ref("mail.mt_note").id,
                author_id=self.env.user.partner_id.id,
            )
            message = _(
                "Transport Order(s) Created: %s",
                Markup(
                    f"""<a href=# data-oe-model=tms.order data-oe-id={tms_order.id}"""
                    f""">{tms_order.name}</a>"""
                ),
            )
            self.message_post(body=message)

    def _action_confirm(self):
        """On SO confirmation, some lines generate TMS orders."""
        result = super()._action_confirm()
        if any(
            sol.product_id.tms_tracking != "no"
            for sol in self.order_line.filtered(
                lambda x: x.display_type not in ("line_section", "line_note")
            )
        ):
            self._tms_generation()
        return result

    def action_view_tms_order(self):
        tms_orders = self.mapped("tms_order_ids")
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "tms.action_tms_dash_order"
        )
        if len(tms_orders) > 1:
            action["domain"] = [("id", "in", tms_orders.ids)]
        elif len(tms_orders) == 1:
            action["views"] = [(self.env.ref("tms.tms_order_view_form").id, "form")]
            action["res_id"] = tms_orders.id
        else:
            action = {"type": "ir.actions.act_window_close"}
        return action
