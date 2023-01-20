# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).


from odoo import _, api, exceptions, fields, models


class TmsRoute(models.Model):
    _name = "tms.route"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Routes"

    name = fields.Char("Route Name", size=64, required=True, index=True)
    departure_id = fields.Many2one("tms.place", "Departure", required=True)
    arrival_id = fields.Many2one("tms.place", "Arrival", required=True)
    distance = fields.Float("Distance (mi./kms)", digits=(14, 4), help="Route distance (mi./kms)", required=True)
    travel_time = fields.Float("Travel Time (hrs)", digits=(14, 4), help="Route travel time (hours)")
    notes = fields.Text()
    active = fields.Boolean(default=True)
    driver_factor_ids = fields.One2many("tms.factor", "route_id", string="Expense driver factor")
    distance_loaded = fields.Float(string="Distance Loaded (mi./km)", required=True)
    distance_empty = fields.Float(string="Distance Empty (mi./km)", required=True)
    route_place_ids = fields.One2many("tms.route.place", "route_id", string="Places")

    @api.depends("distance_empty", "distance")
    @api.onchange("distance_empty")
    def on_change_disance_empty(self):
        for rec in self:
            if rec.distance_empty < 0.0:
                raise exceptions.ValidationError(_("The value must be positive and lower than the distance route."))
            rec.distance_loaded = rec.distance - rec.distance_empty

    @api.depends("distance_loaded", "distance")
    @api.onchange("distance_loaded")
    def on_change_disance_loaded(self):
        for rec in self:
            if rec.distance_loaded < 0.0:
                raise exceptions.ValidationError(_("The value must be positive and lower than the distance route."))
            rec.distance_empty = rec.distance - rec.distance_loaded
