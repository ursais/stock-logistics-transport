# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HrEmployee(models.Model):
    _name = "hr.employee.driver.license"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Driver License"
    _order = "expiration_date desc, employee_id asc"

    name = fields.Char(string="License ID", required=True)
    employee_id = fields.Many2one("hr.employee", required=True, ondelete="cascade")
    license_type = fields.Char()
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

    _sql_constraints = [
        (
            "name_uniq",
            "unique(name)",
            "The license ID must be unique!",
        ),
    ]

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
            days_to_expire = 0
            if rec.expiration_date:
                days_to_expire = max((rec.expiration_date - fields.Date.context_today(self)).days, 0)
            rec.days_to_expire = days_to_expire

    @api.constrains("expiration_date", "emission_date")
    def _check_expiration(self):
        for rec in self:
            if rec.expiration_date and rec.emission_date:
                if rec.expiration_date < rec.emission_date:
                    raise UserError(_("Expiration date must be greater than valid from date!"))
