# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    driver = fields.Boolean(help="Used to define if this person will be used as a Driver")
    property_tms_advance_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Advance Account",
        company_dependent=True,
        domain=[("reconcile", "=", True)],
    )
    property_tms_expense_negative_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Negative Balance Account",
        company_dependent=True,
        domain=[("reconcile", "=", True)],
    )
    license_ids = fields.One2many(
        comodel_name="hr.employee.driver.license",
        inverse_name="employee_id",
        string="Licenses",
    )
    license_expiration_date = fields.Date(compute="_compute_license_expiration_date", store=True)

    @api.depends("license_ids.expiration_date")
    def _compute_license_expiration_date(self):
        for record in self:
            license = record.license_ids.filtered(
                lambda r: r.state == "active"
            ).sorted(key=lambda r: r.expiration_date, reverse=True)
            if license:
                record.license_expiration_date = license[0].expiration_date
            else:
                record.license_expiration_date = fields.Date.context_today(record)

    def action_open_driver_license(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "tms.hr_employee_driver_license_action"
        )
        action.update({
            "context": {"default_employee_id": self.id},
            "domain": [("employee_id", "=", self.id)],
        })
        return action

    @api.constrains("driver")
    def _check_driver(self):
        for record in self:
            if record.driver:
                if not record.address_home_id:
                    raise UserError(_("You must define a Home Address for this Driver"))
