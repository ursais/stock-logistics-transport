# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import _, fields, models
from odoo.exceptions import UserError


class TmsTravelStage(models.Model):
    _name = "tms.travel.stage"
    _description = "Travel Stage"
    _order = "sequence asc"

    name = fields.Char(required=True, copy=False, translate=True)
    sequence = fields.Integer(default=10)
    fold = fields.Boolean(string="Folded in Kanban")
    active = fields.Boolean(default=True)
    description = fields.Html(translate=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("scheduled", "Scheduled"),
            ("progress", "In Progress"),
            ("done", "Done"),
            ("closed", "Closed"),
            ("cancel", "Cancelled"),
        ],
        required=True,
        help="This stage will be used only for the selected state.",
        default="progress",
    )

    def write(self, vals):
        if "active" in vals:
            travels = self.env["tms.travel"].search([("stage_id", "in", self.ids)])
            if travels:
                raise UserError(
                    _("You cannot archive a stage that is in use. Please move your travels to another stage first.")
                )
        return super().write(vals)
