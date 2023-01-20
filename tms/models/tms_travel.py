# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class TmsTravel(models.Model):
    _name = "tms.travel"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Travel"
    _order = "date desc"

    waybill_ids = fields.Many2many("tms.waybill", copy=False)
    driver_factor_ids = fields.One2many(
        "tms.factor", "travel_id", string="Travel Driver Payment Factors", domain=[("category", "=", "driver")]
    )
    name = fields.Char("Travel Number", required=True, copy=False, readonly=True, default="/")
    state = fields.Selection(
        [
            ("draft", "Pending"),
            ("progress", "In Progress"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
            ("closed", "Closed"),
        ],
        tracking=True,
        readonly=True,
        default="draft",
    )
    route_id = fields.Many2one(
        "tms.route", required=True, states={"cancel": [("readonly", True)], "closed": [("readonly", True)]}
    )
    travel_duration = fields.Float(
        compute="_compute_travel_duration", string="Duration Sched", help="Travel Scheduled duration in hours"
    )
    travel_duration_real = fields.Float(
        compute="_compute_travel_duration_real", string="Duration Real", help="Travel Real duration in hours"
    )
    distance_route = fields.Float(related="route_id.distance", string="Route Distance (mi./km)")
    kit_id = fields.Many2one("tms.unit.kit")
    unit_id = fields.Many2one("fleet.vehicle", required=True)
    trailer1_id = fields.Many2one("fleet.vehicle")
    dolly_id = fields.Many2one("fleet.vehicle", domain=[("fleet_type", "=", "dolly")])
    trailer2_id = fields.Many2one("fleet.vehicle", domain=[("fleet_type", "=", "trailer")])
    employee_id = fields.Many2one("hr.employee", "Driver", required=True, domain=[("driver", "=", True)])
    date = fields.Datetime("Date  registered", required=True, default=(fields.Datetime.now))
    date_start = fields.Datetime("Start Sched", default=(fields.Datetime.now))
    date_end = fields.Datetime("End Sched", store=True, compute="_compute_date_end")
    date_start_real = fields.Datetime("Start Real")
    date_end_real = fields.Datetime("End Real")
    distance_driver = fields.Float(
        "Distance traveled by driver (mi./km)", compute="_compute_distance_driver", store=True
    )
    distance_loaded = fields.Float("Distance Loaded (mi./km)")
    distance_empty = fields.Float("Distance Empty (mi./km)")
    odometer = fields.Float("Unit Odometer (mi./km)", readonly=True)
    departure_id = fields.Many2one("tms.place", related="route_id.departure_id", store=True, readonly=True)
    fuel_log_ids = fields.One2many("fleet.vehicle.log.fuel", "travel_id", string="Fuel Vouchers")
    advance_ids = fields.One2many("tms.advance", "travel_id")
    arrival_id = fields.Many2one("tms.place", related="route_id.arrival_id", store=True, readonly=True)
    notes = fields.Text("Description")
    user_id = fields.Many2one("res.users", "Responsable", default=lambda self: self.env.user)
    expense_id = fields.Many2one("tms.expense", "Expense Record", readonly=True)
    is_available = fields.Boolean(compute="_compute_is_available", string="Travel available")
    color = fields.Integer()
    framework = fields.Selection(
        [("unit", "Unit"), ("single", "Single"), ("double", "Double")], compute="_compute_framework"
    )
    partner_ids = fields.Many2many("res.partner", string="Customer", compute="_compute_partner_ids", store=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.user.company_id)

    @api.depends("waybill_ids")
    def _compute_partner_ids(self):
        for rec in self:
            rec.partner_ids = rec.waybill_ids.mapped("partner_id")

    @api.depends("date_start", "travel_duration")
    def _compute_date_end(self):
        for rec in self:
            date_end = False
            if rec.date_start and rec.travel_duration:
                date_end = rec.date_start + timedelta(hours=rec.travel_duration)
            rec.date_end = date_end

    @api.depends("date_start", "date_end")
    def _compute_travel_duration(self):
        for rec in self:
            travel_duration = 0
            if rec.date_start and rec.date_end:
                travel_duration = (rec.date_end - rec.date_start).total_seconds() / 60 / 60
            rec.travel_duration = travel_duration

    @api.depends("date_start_real", "date_end_real")
    def _compute_travel_duration_real(self):
        for rec in self:
            travel_duration_real = 0
            if rec.date_start_real and rec.date_end_real:
                travel_duration_real = (rec.date_end_real - rec.date_start_real).total_seconds() / 60 / 60
            rec.travel_duration_real = travel_duration_real

    @api.onchange("kit_id")
    def _onchange_kit(self):
        self.unit_id = self.kit_id.unit_id.id
        self.trailer2_id = self.kit_id.trailer2_id.id
        self.trailer1_id = self.kit_id.trailer1_id.id
        self.dolly_id = self.kit_id.dolly_id.id
        self.employee_id = self.kit_id.employee_id.id

    @api.onchange("route_id")
    def _onchange_route(self):
        self.travel_duration = self.route_id.travel_time
        self.distance_route = self.route_id.distance
        self.distance_loaded = self.route_id.distance_loaded
        self.distance_empty = self.route_id.distance_empty

    @api.depends("distance_empty", "distance_loaded")
    def _compute_distance_driver(self):
        for rec in self:
            rec.distance_driver = rec.distance_empty + rec.distance_loaded

    def action_draft(self):
        for rec in self:
            rec.state = "draft"

    def action_progress(self):
        for rec in self:
            rec.validate_driver_license()
            rec.validate_vehicle_insurance()
            travels = rec.search(
                [
                    ("state", "=", "progress"),
                    "|",
                    ("employee_id", "=", rec.employee_id.id),
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

    @api.depends()
    def _compute_is_available(self):
        for rec in self:
            objects = ["tms.advance", "fleet.vehicle.log.fuel", "tms.waybill"]
            advances = len(rec.advance_ids)
            fuel_vehicle = len(rec.fuel_log_ids)
            count = 0
            for model in objects:
                if model in ["tms.advance", "fleet.vehicle.log.fuel"]:
                    object_ok = len(rec.env[model].search([("state", "=", "confirmed"), ("travel_id", "=", rec.id)]))
                    if model == "tms.advance" and advances == object_ok or advances == 0:
                        count += 1
                    elif model == "fleet.vehicle.log.fuel" and fuel_vehicle == object_ok or fuel_vehicle == 0:
                        count += 1
                if model == "tms.waybill":
                    object_ok = len(rec.env[model].search([("state", "=", "confirmed"), ("travel_ids", "in", rec.id)]))
                    if len(rec.waybill_ids) == object_ok:
                        count += 1
            if count == 3:
                rec.is_available = True

    @api.depends("trailer1_id", "trailer2_id")
    def _compute_framework(self):
        for rec in self:
            if rec.trailer2_id:
                rec.framework = "double"
            elif rec.trailer1_id:
                rec.framework = "single"
            else:
                rec.framework = "unit"

    def validate_driver_license(self):
        val = self.env["ir.config_parameter"].get_param("driver_license_security_days")
        days = int(val) or 0
        for rec in self:
            if rec.employee_id.days_to_expire <= days:
                raise UserError(
                    _(
                        "You can not Dispatch this Travel because %(employee)s "
                        "Driver s License Validity %(date)s is expired or"
                        " about to expire in next %(days)s days",
                        employee=rec.employee_id.name,
                        date=rec.employee_id.license_expiration,
                        days=val,
                    )
                )

    def validate_vehicle_insurance(self):
        val = self.env["ir.config_parameter"].get_param("tms_vehicle_insurance_security_days")
        xdays = int(val) or 0
        date = datetime.now() + timedelta(days=xdays)
        for rec in self:
            units = [rec.unit_id, rec.trailer1_id, rec.dolly_id, rec.trailer2_id]
            for unit in units:
                if unit.insurance_expiration and unit.insurance_expiration <= date.date():
                    raise UserError(
                        _(
                            "You can not Dispatch this Travel because this Vehicle"
                            " %(vehicle)s Insurance %(date)s is expired or about to expire in "
                            "next %(days)s days",
                            vehicle=unit.name,
                            date=unit.insurance_expiration,
                            days=val,
                        )
                    )
