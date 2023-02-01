# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).


from odoo import fields, models


class TmsUnitKit(models.Model):
    _name = "tms.unit.kit"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "unit_id desc"
    _description = "Units Kits"

    name = fields.Char(required=True, tracking=True)
    unit_id = fields.Many2one("fleet.vehicle", "Unit", required=True, tracking=True)
    trailer1_id = fields.Many2one("fleet.vehicle", "Trailer 1", tracking=True)
    dolly_id = fields.Many2one("fleet.vehicle", "Dolly", tracking=True)
    trailer2_id = fields.Many2one("fleet.vehicle", "Trailer 2", tracking=True)
    driver_id = fields.Many2one("hr.employee", domain=[("driver", "=", True)], tracking=True, company_dependent=True)
    date_start = fields.Datetime(tracking=True)
    date_end = fields.Datetime(tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.user.company_id)

    _sql_constraints = [
        ("name_uniq", "unique(name, company_id)", "The name of the unit kit must be unique per company!"),
    ]
