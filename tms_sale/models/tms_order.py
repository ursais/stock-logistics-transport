# Copyright (C) 2019 Brian McMaster
# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models


class TMSOrder(models.Model):
    _inherit = "tms.order"

    sale_id = fields.Many2one("sale.order")
    sale_line_id = fields.Many2one("sale.order.line")

    def action_view_sales(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "views": [[False, "form"]],
            "res_id": self.sale_line_id.order_id.id or self.sale_id.id,
            "context": {"create": False},
            "name": _("Sales Orders"),
        }

    @api.model
    def write(self, vals):
        for order in self:
            if "stage_id" in vals:
                stage = self.env.ref("tms.tms_stage_order_completed")
                if vals["stage_id"] == stage.id:
                    for line in order.sale_id.order_line:
                        line.qty_delivered = line.product_uom_qty
        return super().write(vals)
