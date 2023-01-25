# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class TmsRoute(models.Model):
    _name = "tms.route"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Routes"

    name = fields.Char("Route Name", required=True)
    notes = fields.Html()
    active = fields.Boolean(default=True)
    driver_factor_ids = fields.One2many("tms.factor", "driver_route_id")
    customer_factor_ids = fields.One2many("tms.factor", "customer_route_id")
    distance = fields.Float(
        string="Distance (mi./kms)",
        compute="_compute_distance",
        store=True,
    )
    distance_loaded = fields.Float(string="Distance Loaded (mi./km)", required=True)
    distance_empty = fields.Float(string="Distance Empty (mi./km)", required=True)
    travel_time = fields.Float("Travel Time (hrs)", help="Route travel time (hours)")
    travel_ids = fields.One2many("tms.travel", "route_id")
    partner_ids = fields.Many2many("res.partner", string="Customers", compute="_compute_partner_ids", store=True)

    @api.constrains("distance_loaded", "distance_empty", "travel_time")
    def _check_route(self):
        if self.distance <= 0.0:
            raise UserError(_("Distance must be greater than zero."))
        if self.travel_time <= 0.0:
            raise UserError(_("Travel Time must be greater than zero."))

    @api.depends("customer_factor_ids", "customer_factor_ids.partner_id")
    def _compute_partner_ids(self):
        for rec in self:
            rec.partner_ids = rec.customer_factor_ids.mapped("partner_id")

    @api.depends("distance_empty", "distance_loaded")
    def _compute_distance(self):
        for rec in self:
            rec.distance_loaded = max(rec.distance_loaded, 0.0)
            rec.distance_empty = max(rec.distance_empty, 0.0)
            rec.distance = rec.distance_empty + rec.distance_loaded

    def write(self, values):
        validate_fields = {
            "name": _("Name"),
            "distance": _("Distance"),
            "distance_loaded": _("Distance Loaded"),
            "distance_empty": _("Distance Empty"),
            "travel_time": _("Travel Time"),
        }
        for field, name in validate_fields.items():
            if field in values and self.mapped("travel_ids").filtered(lambda t: t.state != "cancel"):
                raise UserError(_("You can not change the %(name)s of a route with travels.", name=name))
        return super().write(values)
