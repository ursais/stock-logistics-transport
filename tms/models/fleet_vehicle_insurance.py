# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class FleetVehicleInsurance(models.Model):
    _name = "fleet.vehicle.insurance"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Vehicle Insurance"
    _order = "expiration_date desc, unit_id asc"

    name = fields.Char(string="Insurance Policy", required=True)
    partner_id = fields.Many2one("res.partner", required=True)
    unit_id = fields.Many2one("fleet.vehicle", required=True)
    days_to_expire = fields.Integer(compute="_compute_days_to_expire")
    emission_date = fields.Date(required=True)
    expiration_date = fields.Date(required=True)
    state = fields.Selection(
        [
            ("active", "Active"),
            ("expired", "Expired"),
        ],
        compute="_compute_state",
    )

    @api.depends("expiration_date")
    def _compute_state(self):
        for rec in self:
            if rec.expiration_date:
                if rec.expiration_date < fields.Date.context_today(self):
                    rec.state = "expired"
                else:
                    rec.state = "active"
            else:
                rec.state = "active"

    @api.depends("expiration_date")
    def _compute_days_to_expire(self):
        for rec in self:
            if rec.expiration_date:
                days_to_expire = (rec.expiration_date - fields.Date.context_today(self)).days
                if days_to_expire < 0:
                    days_to_expire = 0
            else:
                days_to_expire = 0
            rec.days_to_expire = days_to_expire

    @api.constrains("expiration_date", "emission_date")
    def _check_expiration(self):
        for rec in self:
            if rec.expiration_date and rec.emission_date:
                if rec.expiration_date < rec.emission_date:
                    raise UserError(_("Expiration date must be greater than valid from date!"))
