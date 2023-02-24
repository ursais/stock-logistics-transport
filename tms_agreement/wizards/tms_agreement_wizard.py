# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class TmsAgreementWizard(models.TransientModel):
    _name = "tms.agreement.wizard"
    _description = "TMS Agreement Wizard"

    agreement_id = fields.Many2one("tms.agreement", string="Agreement", required=True)
    kit_id = fields.Many2one("tms.unit.kit", string="Unit Kit")
    driver_id = fields.Many2one("hr.employee", string="Driver", required=True, domain=[("driver", "=", True)])
    unit_id = fields.Many2one("fleet.vehicle", string="Unit", required=True, domain=[("fleet_type", "=", "tractor")])
    trailer1_id = fields.Many2one("fleet.vehicle", string="Trailer 1", domain=[("fleet_type", "=", "trailer")])
    trailer2_id = fields.Many2one("fleet.vehicle", string="Trailer 2", domain=[("fleet_type", "=", "trailer")])
    dolly_id = fields.Many2one("fleet.vehicle", string="Dolly", domain=[("fleet_type", "=", "dolly")])
    date_start = fields.Datetime(required=True)

    @api.onchange("kit_id")
    def _onchange_kit_id(self):
        self.update(
            {
                "driver_id": self.kit_id.driver_id.id,
                "unit_id": self.kit_id.unit_id.id,
                "trailer1_id": self.kit_id.trailer1_id.id,
                "trailer2_id": self.kit_id.trailer2_id.id,
                "dolly_id": self.kit_id.dolly_id.id,
            }
        )

    def _prepare_travel(self):
        self.ensure_one()
        return {
            "agreement_id": self.agreement_id.id,
            "partner_ids": [(6, 0, self.agreement_id.partner_id.ids)],
            "driver_id": self.driver_id.id,
            "unit_id": self.unit_id.id,
            "trailer1_id": self.trailer1_id.id,
            "trailer2_id": self.trailer2_id.id,
            "dolly_id": self.dolly_id.id,
            "date_start": self.date_start,
            "route_id": self.agreement_id.route_id.id,
            "kit_id": self.kit_id.id,
            "waybill_ids": self._prepare_waybill(),
            "fuel_ids": self._prepare_fuel(),
            "advance_ids": self._prepare_advance(),
        }

    def _prepare_waybill(self):
        return [(0, 0, self._prepare_waybill_vals())]

    def _prepare_waybill_vals(self):
        return {
            "agreement_id": self.agreement_id.id,
            "partner_id": self.agreement_id.partner_id.id,
            "invoice_partner_id": self.agreement_id.invoice_partner_id.id,
            "partner_order_id": self.agreement_id.partner_order_id.id,
            "currency_id": self.agreement_id.currency_id.id,
            "transportable_line_ids": self._prepare_transportable_lines(),
        }

    def _prepare_transportable_lines(self):
        return [(0, 0, self._prepare_transportable_lines_vals())]

    def _prepare_transportable_lines_vals(self):
        return {
            "transportable_id": self.agreement_id.transportable_id.id,
            "name": self.agreement_id.transportable_id.name,
            "product_uom_id": self.agreement_id.transportable_id.product_uom_id.id,
        }

    def _prepare_fuel(self):
        fuel_list = []
        if not self.agreement_id.agreement_fuel_ids:
            return fuel_list
        for fuel in self.agreement_id.agreement_fuel_ids:
            fuel_list.append((0, 0, self._prepare_fuel_vals(fuel)))
        return fuel_list

    def _prepare_fuel_vals(self, fuel):
        analytic_account_id = (
            fuel.analytic_account_id.id if fuel.analytic_account_id else self.unit_id.analytic_account_id.id
        )
        analytic_tag_ids = fuel.analytic_tag_ids.ids if fuel.analytic_tag_ids else self.unit_id.analytic_tag_ids.ids
        return {
            "agreement_id": self.agreement_id.id,
            "partner_id": fuel.partner_id.id,
            "product_id": fuel.product_id.id,
            "product_uom_id": fuel.product_uom_id.id,
            "analytic_account_id": analytic_account_id,
            "price_unit": 1.0,
            "analytic_tag_ids": [(6, 0, analytic_tag_ids)],
        }

    def _prepare_advance(self):
        advance_list = []
        if not self.agreement_id.agreement_advance_ids:
            return advance_list
        for advance in self.agreement_id.agreement_advance_ids:
            advance_list.append((0, 0, self._prepare_advance_vals(advance)))
        return advance_list

    def _prepare_advance_vals(self, advance):
        return {
            "agreement_id": self.agreement_id.id,
            "amount": advance.amount,
            "currency_id": advance.currency_id.id,
            "product_id": advance.product_id.id,
            "auto_expense": advance.auto_expense,
        }

    def action_create_documents(self):
        self.ensure_one()
        travel_vals = self._prepare_travel()
        travel = self.env["tms.travel"].create(travel_vals)
        travel._onchange_route_date_start()
        action = self.env["ir.actions.actions"]._for_xml_id("tms.open_view_tms_travel_form")
        action["res_id"] = travel.id
        return action
