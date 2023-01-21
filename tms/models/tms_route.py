# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class TmsRoute(models.Model):
    _name = "tms.route"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Routes"

    name = fields.Char("Route Name", required=True)
    notes = fields.Html()
    active = fields.Boolean(default=True)
    driver_factor_ids = fields.One2many("tms.factor", "route_id", string="Expense driver factor")
    distance = fields.Float(
        string="Distance (mi./kms)",
        help="Route distance (mi./kms)",
        required=True,
        compute="_compute_distance",
        inverse="_inverse_distance",
        store=True,
    )
    distance_loaded = fields.Float(string="Distance Loaded (mi./km)", required=True)
    distance_empty = fields.Float(
        string="Distance Empty (mi./km)",
        required=True,
        help="Route distance empty (mi./km)",
        compute="_compute_distance_empty",
        inverse="_inverse_distance_empty",
        store=True,
    )
    travel_time = fields.Float("Travel Time (hrs)", help="Route travel time (hours)")

    @api.depends("distance_empty", "distance_loaded")
    def _compute_distance(self):
        for rec in self:
            rec.distance_empty = max(rec.distance_empty, 0.0)
            rec.distance_loaded = max(rec.distance_loaded, 0.0)
            rec.distance = rec.distance_empty + rec.distance_loaded

    def _inverse_distance(self):
        for rec in self:
            rec.distance = max(rec.distance, 0.0)
            if rec.distance_loaded:
                rec.distance_empty = rec.distance - rec.distance_loaded
            if rec.distance_empty:
                rec.distance_loaded = rec.distance - rec.distance_empty

    @api.depends("distance", "distance_loaded")
    def _compute_distance_empty(self):
        for rec in self:
            rec.distance = max(rec.distance, 0.0)
            rec.distance_loaded = max(rec.distance_loaded, 0.0)
            rec.distance_empty = rec.distance - rec.distance_loaded

    def _inverse_distance_empty(self):
        for rec in self:
            rec.distance_loaded = max(rec.distance_loaded, 0.0)
            rec.distance_empty = (rec.distance_empty, 0.0)
            rec.distance = rec.distance_loaded + rec.distance_empty
