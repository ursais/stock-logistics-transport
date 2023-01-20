# Copyright 2012, Israel Cruz Argil, Argil Consulting
# Copyright 2016, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    driver = fields.Boolean(help="Used to define if this person will be used as a Driver")
    tms_advance_account_id = fields.Many2one("account.account", "Advance Account", company_dependent=True)
    tms_expense_negative_account_id = fields.Many2one(
        "account.account", "Negative Balance Account", company_dependent=True
    )
    driver_license = fields.Char(string="License ID")
    license_type = fields.Char()
    days_to_expire = fields.Integer(compute="_compute_days_to_expire")
    income_percentage = fields.Float()
    license_valid_from = fields.Date()
    license_expiration = fields.Date()

    @api.depends("license_expiration")
    def _compute_days_to_expire(self):
        for rec in self:
            date = fields.Date.context_today(self)
            if rec.license_expiration:
                date = rec.license_expiration
            now = fields.Date.context_today(self)
            delta = date - now
            rec.days_to_expire = delta.days if delta.days > 0 else 0
