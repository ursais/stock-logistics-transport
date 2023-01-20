# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HrEmployee(models.Model):
    _name = "hr.employee.driver.license"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Driver License"
    _order = "license_expiration desc, employee_id asc"

    name = fields.Char(string="License ID")
    employee_id = fields.Many2one("hr.employee", required=True)
    license_type = fields.Char()
    days_to_expire = fields.Integer(compute="_compute_days_to_expire")
    license_valid_from = fields.Date()
    license_expiration = fields.Date(required=True)
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

    @api.depends("license_expiration")
    def _compute_state(self):
        for rec in self:
            if rec.license_expiration:
                if rec.license_expiration < fields.Date.context_today(self):
                    rec.state = "expired"
                else:
                    rec.state = "active"
            else:
                rec.state = "active"

    @api.depends("license_expiration")
    def _compute_days_to_expire(self):
        for rec in self:
            if rec.license_expiration:
                days_to_expire = (rec.license_expiration - fields.Date.context_today(self)).days
                if days_to_expire < 0:
                    days_to_expire = 0
            else:
                days_to_expire = 0
            rec.days_to_expire = days_to_expire

    @api.constrains("license_expiration", "license_valid_from")
    def _check_expiration(self):
        for rec in self:
            if rec.license_expiration and rec.license_valid_from:
                if rec.license_expiration < rec.license_valid_from:
                    raise UserError(_("Expiration date must be greater than valid from date!"))
