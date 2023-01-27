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
        ondelete="restrict",
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
    route_travel_time = fields.Float(string="Duration Sched", readonly=True)
    route_distance = fields.Float(readonly=True)
    route_distance_loaded = fields.Float(readonly=True)
    route_distance_empty = fields.Float(readonly=True)
    distance = fields.Float("Distance traveled", compute="_compute_distance", store=True)
    distance_loaded = fields.Float()
    distance_empty = fields.Float()
    odometer = fields.Float(readonly=True)
    odometer_unit = fields.Selection(related="unit_id.odometer_unit", store=True)
    notes = fields.Html("Description")
    user_id = fields.Many2one("res.users", "Responsible", default=lambda self: self.env.user, required=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.user.company_id)
    error_message = fields.Html(compute="_compute_error_message")
    stage_id = fields.Many2one(
        comodel_name="tms.travel.stage",
        copy=False,
        tracking=True,
        ondelete="restrict",
        default=lambda self: self.env["tms.travel.stage"].search(
            [("state", "=", "draft")], limit=1, order="sequence asc"
        ),
        group_expand="_group_expand_stage_id",
    )
    # waybill_ids = fields.Many2many("tms.waybill", copy=False)
    fuel_ids = fields.One2many("tms.fuel", "travel_id", string="Fuel Vouchers")
    advance_ids = fields.One2many("tms.advance", "travel_id", string="Advances")
    partner_ids = fields.Many2many("res.partner", string="Customers", domain=[("is_company", "=", True)])
    # expense_id = fields.Many2one("tms.expense", "Expense Record", readonly=True)

    def _group_expand_stage_id(self, stages, domain, order):
        return stages.search([], order="sequence asc")

    @api.depends("date_start_real", "date_end_real")
    def _compute_travel_time_real(self):
        for rec in self:
            travel_time_real = 0
            if rec.date_start_real and rec.date_end_real:
                travel_time_real = (rec.date_end_real - rec.date_start_real).total_seconds() / 60 / 60
            rec.travel_time_real = travel_time_real

    @api.onchange("partner_ids")
    def _onchange_partner_ids(self):
        if self.partner_ids and len(self.partner_ids) == 1:
            routes = self.route_id.search([("partner_ids", "in", self.partner_ids.ids)])
            self.route_id = routes if len(routes) == 1 else False
        else:
            self.route_id = False

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
                "route_travel_time": self.route_id.travel_time,
                "route_distance": self.route_id.distance,
                "route_distance_loaded": self.route_id.distance_loaded,
                "route_distance_empty": self.route_id.distance_empty,
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
        if self.driver_id and (
            self.driver_id.active_license_id
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
            if unit.active_insurance_policy_id and (
                unit.active_insurance_policy_id.days_to_expire <= insurance_security_days
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
                "<strong>This travel cannot be dispateched due to the following errors:</strong><br/>%(errors)s",
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

    def _get_stage_by_state(self, state):
        return self.env["tms.travel.stage"].search([("state", "=", state)], limit=1, order="sequence asc").id

    def action_draft(self):
        for rec in self:
            if rec.state not in ["cancel", "scheduled"]:
                raise UserError(_("Only canceled or scheduled travels can be set to draft."))
            rec.write(
                {
                    "state": "draft",
                    "stage_id": self._get_stage_by_state("draft"),
                }
            )

    def action_schedule(self):
        for rec in self:
            if rec.error_message:
                raise UserError(rec.error_message)
            rec.write(
                {
                    "state": "scheduled",
                    "stage_id": self._get_stage_by_state("scheduled"),
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
                    "stage_id": self._get_stage_by_state("progress"),
                }
            )

    def action_done(self):
        for rec in self:
            if not rec.distance:
                raise UserError(_("You must set the distance traveled."))
            odometer = self.env["fleet.vehicle.odometer"].create(
                {
                    "date": fields.Date.context_today(self),
                    "travel_id": rec.id,
                    "vehicle_id": rec.unit_id.id,
                    "last_odometer": rec.unit_id.odometer,
                    "distance": rec.distance,
                    "value": rec.unit_id.odometer + rec.distance,
                }
            )
            rec.write(
                {
                    "state": "done",
                    "date_end_real": fields.Datetime.now(),
                    "odometer": odometer.value,
                    "stage_id": self._get_stage_by_state("done"),
                }
            )

    def action_cancel(self):
        for rec in self:
            advances = rec.advance_ids.filtered(lambda a: a.state != "cancel")
            fuel = rec.fuel_ids.filtered(lambda f: f.state != "cancel")
            if advances or fuel:
                raise UserError(
                    _(
                        "You need to cancel the advances or fuel logs related to this travel before canceling it."
                    )
                )
            rec.write(
                {
                    "state": "cancel",
                    "stage_id": self._get_stage_by_state("cancel"),
                }
            )

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
            if vals.get("stage_id") and vals.get("state"):
                stage = self.env["tms.travel.stage"].browse(vals.get("stage_id"))
                if stage.state != vals.get("state"):
                    states = dict(self._fields["state"]._description_selection(self.env))
                    stages = self.env["tms.travel.stage"].search([("state", "=", vals.get("state"))]).mapped("name")
                    raise UserError(
                        _(
                            "You can only change the stage that are valid for %(state)s state.\n%(stages)s",
                            state=states.get(vals.get("state")),
                            stages="\n".join(stages),
                        )
                    )
            elif vals.get("stage_id"):
                stage = self.env["tms.travel.stage"].browse(vals.get("stage_id"))
                if stage.state != rec.state:
                    states = dict(self._fields["state"]._description_selection(self.env))
                    stages = self.env["tms.travel.stage"].search([("state", "=", rec.state)]).mapped("name")
                    raise UserError(
                        _(
                            "You can only change the stage that are valid for %(state)s state.\n%(stages)s",
                            state=states.get(rec.state),
                            stages="\n".join(stages),
                        )
                    )
        return super().write(vals)
