# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_tms_operating_unit = fields.Boolean(
        string="Operating Unit in TMS",
    )
    module_tms_fuel_ieps = fields.Boolean(
        string="IEPS in TMS Fuel",
    )
    module_tms_driver_loan = fields.Boolean(
        string="Driver Loans in TMS",
    )
    module_tms_tier_validation = fields.Boolean(
        string="Use Tier Validation for TMS Documents",
    )
    driver_license_security_days = fields.Integer(
        related="company_id.driver_license_security_days",
        readonly=False,
    )
    insurance_security_days = fields.Integer(
        related="company_id.insurance_security_days",
        readonly=False,
    )
    advance_journal_id = fields.Many2one(
        related="company_id.advance_journal_id",
        readonly=False,
    )
    expense_journal_id = fields.Many2one(
        related="company_id.expense_journal_id",
        readonly=False,
    )
    advance_account_id = fields.Many2one(
        related="company_id.advance_account_id",
        readonly=False,
    )
    fuel_prepaid_journal_id = fields.Many2one(
        related="company_id.fuel_prepaid_journal_id",
        readonly=False,
    )
    expense_negative_account_id = fields.Many2one(
        related="company_id.expense_negative_account_id",
        readonly=False,
    )
