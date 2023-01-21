# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class TmsTravel(models.Model):
    _name = "tms.travel"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Travel"
    _order = "date_start desc"

    name = fields.Char("Travel Number", required=True, copy=False, readonly=True, default="/")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("scheduled", "Scheduled"),
            ("progress", "In Progress"),
            ("done", "Done"),
            ("closed", "Closed"),
            ("cancel", "Cancelled"),
        ],
        tracking=True,
        readonly=True,
        default="draft",
    )
    route_id = fields.Many2one(
        "tms.route",
        required=True,
    )
    kit_id = fields.Many2one("tms.unit.kit")
    unit_id = fields.Many2one("fleet.vehicle", required=True, domain=[("fleet_type", "=", "tractor")])
    trailer1_id = fields.Many2one("fleet.vehicle", domain=[("fleet_type", "=", "trailer")])
    dolly_id = fields.Many2one("fleet.vehicle", domain=[("fleet_type", "=", "dolly")])
    trailer2_id = fields.Many2one("fleet.vehicle", domain=[("fleet_type", "=", "trailer")])
    driver_id = fields.Many2one("hr.employee", "Driver", required=True, domain=[("driver", "=", True)])
    date_start = fields.Datetime(
        "Start Sched",
        default=(fields.Datetime.now),
        copy=False,
    )
    date_end = fields.Datetime(
        string="End Sched",
        compute="_compute_date_end",
        inverse="_inverse_date_end",
        store=True,
    )
    date_start_real = fields.Datetime("Start Real", readonly=True, copy=False)
    date_end_real = fields.Datetime("End Real", readonly=True, copy=False)
    travel_time_real = fields.Float(
        compute="_compute_travel_time_real", string="Duration Real", help="Travel Real duration in hours"
    )
    route_travel_time = fields.Float(
        string="Duration Sched",
        help="Travel Scheduled duration in hours, based on route travel time",
        related="route_id.travel_time",
        store=True,
    )
    route_distance = fields.Float(
        related="route_id.distance",
        string="Route Distance (mi./km)",
        store=True,
    )
    route_distance_loaded = fields.Float(
        related="route_id.distance_loaded",
        string="Route Distance Loaded (mi./km)",
        store=True,
    )
    route_distance_empty = fields.Float(related="route_id.distance_empty", string="Route Distance Empty (mi./km)")
    distance = fields.Float("Distance traveled by driver (mi./km)", compute="_compute_distance", store=True)
    distance_loaded = fields.Float("Distance Loaded (mi./km)")
    distance_empty = fields.Float("Distance Empty (mi./km)")
    odometer = fields.Float("Unit Odometer (mi./km)", readonly=True)
    notes = fields.Html("Description")
    user_id = fields.Many2one("res.users", "Responsible", default=lambda self: self.env.user, required=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.user.company_id)
    error_message = fields.Html(compute="_compute_error_message")
    # waybill_ids = fields.Many2many("tms.waybill", copy=False)
    # fuel_log_ids = fields.One2many("fleet.vehicle.log.fuel", "travel_id", string="Fuel Vouchers")
    # advance_ids = fields.One2many("tms.advance", "travel_id")
    # expense_id = fields.Many2one("tms.expense", "Expense Record", readonly=True)
    # partner_ids = fields.Many2many("res.partner", string="Customer", compute="_compute_partner_ids", store=True)

    # @api.depends("waybill_ids")
    # def _compute_partner_ids(self):
    #     for rec in self:
    #         rec.partner_ids = rec.waybill_ids.mapped("partner_id")

    @api.depends("date_start_real", "date_end_real")
    def _compute_travel_time_real(self):
        for rec in self:
            travel_time_real = 0
            if rec.date_start_real and rec.date_end_real:
                travel_time_real = (rec.date_end_real - rec.date_start_real).total_seconds() / 60 / 60
            rec.travel_time_real = travel_time_real

    @api.onchange("kit_id")
    def _onchange_kit(self):
        self.update(
            {
                "unit_id": self.kit_id.unit_id.id,
                "trailer2_id": self.kit_id.trailer2_id.id,
                "trailer1_id": self.kit_id.trailer1_id.id,
                "dolly_id": self.kit_id.dolly_id.id,
                "driver_id": self.kit_id.driver_id.id,
            }
        )

    @api.depends("date_start", "route_id")
    def _compute_date_end(self):
        for rec in self:
            rec.date_end = rec.date_start + timedelta(hours=rec.route_id.travel_time)

    def _inverse_date_end(self):
        for rec in self:
            rec.date_start = rec.date_end - timedelta(hours=rec.route_id.travel_time)

    @api.onchange("route_id", "date_start")
    def _onchange_route_date_start(self):
        self.update(
            {
                "date_end": self.date_start + timedelta(hours=self.route_id.travel_time),
            }
        )

    @api.depends("distance_empty", "distance_loaded")
    def _compute_distance(self):
        for rec in self:
            rec.distance = rec.distance_empty + rec.distance_loaded

    @api.depends("driver_id", "unit_id", "trailer1_id", "dolly_id", "trailer2_id", "date_start")
    def _compute_error_message(self):
        for rec in self:
            rec.error_message = rec._get_error_message_html()

    def _get_error_message_list(self):
        self.ensure_one()
        error_message = []
        if self.driver_id and not self.driver_id.active_license_id:
            error_message.append(
                _(
                    "The driver %(driver_name)s has no driver license.",
                    driver_name=self.driver_id.name,
                )
            )
        driver_license_security_days = self.company_id.driver_license_security_days
        if (
            self.driver_id
            and self.driver_id.active_license_id
            and self.driver_id.active_license_id.days_to_expire <= driver_license_security_days
            or self.driver_id.active_license_id.emission_date >= self.date_start.date()
        ):
            error_message.append(
                _(
                    "Invalid driver licence for %(driver_name)s. "
                    "Valid from %(emission_date)s to %(expiration_date)s.",
                    driver_name=self.driver_id.name,
                    emission_date=self.driver_id.active_license_id.emission_date,
                    expiration_date=self.driver_id.active_license_id.expiration_date,
                )
            )
        for unit in self.unit_id + self.trailer1_id + self.trailer2_id + self.dolly_id:
            if not unit.active_insurance_policy_id:
                error_message.append(
                    _(
                        "The unit %(unit_name)s has no insurance policy.",
                        unit_name=unit.name,
                    )
                )
            insurance_security_days = self.company_id.insurance_security_days
            if (
                unit.active_insurance_policy_id
                and unit.active_insurance_policy_id.days_to_expire <= insurance_security_days
                or unit.active_insurance_policy_id.emission_date >= self.date_start.date()
            ):
                error_message.append(
                    _(
                        "Invalid Insurance Policy for unit %(unit_name)s. "
                        "Valid from %(emission_date)s to %(expiration_date)s.",
                        unit_name=unit.name,
                        emission_date=unit.active_insurance_policy_id.emission_date,
                        expiration_date=unit.active_insurance_policy_id.expiration_date,
                    )
                )
        return error_message

    def _get_error_message_html(self):
        self.ensure_one()
        error_message = self._get_error_message_list()
        return (
            _(
                "This travel cannot be dispateched due to the following errors:<br/>%(errors)s",
                errors="".join(["<li>%s</li>" % error for error in error_message]),
            )
            if error_message
            else False
        )

    def _get_error_message_text(self):
        self.ensure_one()
        error_message = self._get_error_message_list()
        return (
            _(
                "This travel cannot be dispateched due to the following errors:\n%(errors)s",
                errors="\n".join(error_message),
            )
            if error_message
            else False
        )

    def action_draft(self):
        for rec in self:
            if rec.state not in ["cancel", "scheduled"]:
                raise UserError(_("Only canceled or scheduled travels can be set to draft."))
            rec.state = "draft"

    def action_schedule(self):
        for rec in self:
            if rec.error_message:
                raise UserError(rec.error_message)
            rec.write(
                {
                    "state": "scheduled",
                }
            )

    def action_progress(self):
        for rec in self:
            if rec.error_message:
                raise UserError(rec._get_error_message_text())
            travels = rec.search(
                [
                    ("state", "=", "progress"),
                    "|",
                    ("driver_id", "=", rec.driver_id.id),
                    ("unit_id", "=", rec.unit_id.id),
                ]
            )
            if len(travels) >= 1:
                raise UserError(_("The unit or driver are already in use!"))
            rec.write(
                {
                    "state": "progress",
                    "date_start_real": fields.Datetime.now(),
                }
            )

    def action_done(self):
        for rec in self:
            odometer = self.env["fleet.vehicle.odometer"].create(
                {
                    "travel_id": rec.id,
                    "vehicle_id": rec.unit_id.id,
                    "last_odometer": rec.unit_id.odometer,
                    "distance": rec.distance_driver,
                    "current_odometer": rec.unit_id.odometer + rec.distance_driver,
                    "value": rec.unit_id.odometer + rec.distance_driver,
                }
            )
            rec.write(
                {
                    "state": "done",
                    "date_end_real": fields.Datetime.now(),
                    "odometer": odometer.current_odometer,
                }
            )

    def action_cancel(self):
        for rec in self:
            advances = rec.advance_ids.search([("state", "!=", "cancel"), ("travel_id", "=", rec.id)])
            fuel_log = rec.fuel_log_ids.search([("state", "!=", "cancel"), ("travel_id", "=", rec.id)])
            if len(advances) >= 1 or len(fuel_log) >= 1:
                raise UserError(
                    _(
                        "If you want to cancel this travel,"
                        " you must cancel the fuel logs or the advances "
                        "attached to this travel"
                    )
                )
            rec.state = "cancel"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = self.env["ir.sequence"].next_by_code("tms.travel") or _("New")
        return super().create(vals_list)

    def write(self, vals):
        for rec in self:
            if vals.get("date_start") and rec.state != "draft":
                raise UserError(_("You can only change the scheduled date of a travel in Draft state"))
        return super().write(vals)
