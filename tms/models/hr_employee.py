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
        help="Account used to register advances in the expense, "
        "if not set it will take the default account from the company",
    )
    property_tms_expense_negative_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Negative Balance Account",
        company_dependent=True,
        domain=[("reconcile", "=", True)],
        help="Account used to register negative balance in the expense, "
        "if not set it will take the default account from the company",
    )
    license_ids = fields.One2many(
        comodel_name="hr.employee.driver.license",
        inverse_name="employee_id",
        string="Licenses",
    )
    active_license_id = fields.Many2one(
        comodel_name="hr.employee.driver.license",
        compute="_compute_active_license_id",
    )
    license_expiration_date = fields.Date(compute="_compute_license_expiration_date", store=True)

    @api.depends("license_ids.expiration_date")
    def _compute_active_license_id(self):
        for record in self:
            active_license = record.license_ids.filtered(lambda r: r.state == "active").sorted(
                key=lambda r: r.expiration_date, reverse=True
            )
            if active_license:
                record.active_license_id = active_license[0]
            else:
                record.active_license_id = False

    @api.depends("active_license_id", "active_license_id.expiration_date")
    def _compute_license_expiration_date(self):
        for record in self:
            if record.active_license_id:
                record.license_expiration_date = record.active_license_id.expiration_date
            else:
                record.license_expiration_date = fields.Date.context_today(record)

    def action_open_driver_license(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("tms.hr_employee_driver_license_action")
        action.update(
            {
                "context": {"default_employee_id": self.id},
                "domain": [("employee_id", "=", self.id)],
            }
        )
        return action

    @api.constrains("driver")
    def _check_driver(self):
        for record in self:
            if record.driver and not record.address_home_id:
                raise UserError(_("You must define a Home Address for this Driver"))
