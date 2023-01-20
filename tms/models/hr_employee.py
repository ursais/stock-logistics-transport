# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# # License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

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

    @api.constrains("driver")
    def _check_driver(self):
        for record in self:
            if record.driver:
                if not record.address_home_id:
                    raise UserError(_("You must define a Home Address for this Driver"))
