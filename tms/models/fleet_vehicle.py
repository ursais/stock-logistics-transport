# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"
    _order = "economic_number asc, fleet_type asc, license_plate asc"

    fleet_type = fields.Selection(
        [("tractor", "Motorized Unit"), ("trailer", "Trailer"), ("dolly", "Dolly"), ("other", "Other")],
        default="tractor",
        string="Unit Fleet Type",
    )
    economic_number = fields.Char(copy=False)
    policy_ids = fields.One2many("fleet.vehicle.insurance", "unit_id", string="Policies")
    insurance_policy_expiration_date = fields.Date(
        compute="_compute_insurance_policy_expiration_date",
        store=True,
        default=fields.Date.context_today,
    )
    active_insurance_policy_id = fields.Many2one(
        "fleet.vehicle.insurance",
        compute="_compute_active_insurance_policy_id",
    )
    insurance_ids = fields.One2many("fleet.vehicle.insurance", "unit_id", string="Insurances")
    analytic_account_id = fields.Many2one(
        "account.analytic.account", company_dependent=True, check_company=True, copy=False
    )
    analytic_tag_ids = fields.Many2many("account.analytic.tag", string="Analytic Tags", copy=False)

    _sql_constraints = [
        (
            "economic_number_company_uniq",
            "unique (economic_number, company_id)",
            "You can not have two vehicles for the same company and economic number",
        ),
    ]

    def action_open_insurance_policy(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("tms.fleet_vehicle_insurance_action")
        action.update(
            {
                "context": {"default_unit_id": self.id},
                "domain": [("unit_id", "=", self.id)],
            }
        )
        return action

    @api.depends("policy_ids", "policy_ids.expiration_date")
    def _compute_active_insurance_policy_id(self):
        for record in self:
            policy = record.policy_ids.filtered(lambda r: r.state == "active").sorted(
                key=lambda r: r.expiration_date, reverse=True
            )
            if policy:
                record.active_insurance_policy_id = policy[0].id
            else:
                record.active_insurance_policy_id = False

    @api.depends("active_insurance_policy_id", "active_insurance_policy_id.expiration_date")
    def _compute_insurance_policy_expiration_date(self):
        for record in self:
            if record.insurance_policy_expiration_date:
                record.insurance_policy_expiration_date = record.active_insurance_policy_id.expiration_date
            else:
                record.insurance_policy_expiration_date = fields.Date.context_today(record)

    @api.depends("model_id.brand_id.name", "model_id.name", "license_plate", "economic_number")
    def _compute_vehicle_name(self):
        res = super()._compute_vehicle_name()
        for record in self:
            if record.economic_number:
                record.name = record.economic_number + "/" + record.name
        return res

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        if default is None:
            default = {}
        default.update(
            {
                "economic_number": False,
                "license_plate": False,
            }
        )
        return super().copy(default)
