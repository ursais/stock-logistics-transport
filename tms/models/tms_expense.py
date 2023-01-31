# Copyright 2016-2023, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class TmsExpense(models.Model):
    _name = "tms.expense"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Travel Expenses"
    _order = "name desc"

    name = fields.Char(readonly=True)
    driver_id = fields.Many2one(
        "hr.employee",
        "Driver",
        required=True,
    )
    travel_ids = fields.Many2many("tms.travel", string="Travels")
    unit_id = fields.Many2one("fleet.vehicle", required=True)
    unit_ids = fields.Many2many("fleet.vehicle", string="Units", compute="_compute_unit_ids")
    currency_id = fields.Many2one(
        "res.currency",
        required=True,
        default=lambda self: self.env.user.company_id.currency_id,
    )
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed"), ("cancel", "Cancelled")],
        readonly=True,
        tracking=True,
        default="draft",
    )
    date = fields.Date(required=True, default=fields.Date.context_today)
    expense_line_ids = fields.One2many("tms.expense.line", "expense_id", "Expense Lines")
    amount_real_expense = fields.Monetary(string="Expenses", compute="_compute_amounts", store=True)
    fuel_qty = fields.Float(compute="_compute_amounts", store=True)
    amount_fuel = fields.Monetary(string="Cost of Fuel", compute="_compute_amounts", store=True)
    amount_tax_fuel = fields.Monetary(string="Taxes on Fuel", compute="_compute_amounts", store=True)
    amount_total_fuel = fields.Monetary(string="Total Fuel", compute="_compute_amounts", store=True)
    amount_other_income = fields.Monetary(string="Other Income", compute="_compute_amounts", store=True)
    amount_salary = fields.Monetary(string="Salary", compute="_compute_amounts", store=True)
    amount_net_salary = fields.Monetary(string="Net Salary", compute="_compute_amounts", store=True)
    amount_salary_retention = fields.Monetary(string="Salary Retentions", compute="_compute_amounts", store=True)
    amount_salary_discount = fields.Monetary(string="Salary Discounts", compute="_compute_amounts", store=True)
    amount_total_driver_expenses = fields.Monetary(
        string="Total Driver Expenses", compute="_compute_amounts", store=True
    )
    amount_advance = fields.Monetary(string="Total Advances", compute="_compute_amounts", store=True)
    amount_balance = fields.Monetary(string="Balance", compute="_compute_amounts", store=True)
    amount_tax_real = fields.Monetary(string="Taxes (Real)", compute="_compute_amounts", store=True)
    amount_total_real = fields.Monetary(string="Total (Real)", compute="_compute_amounts", store=True)
    amount_advance_expense_balance = fields.Monetary(string="Expense Balance", compute="_compute_amounts", store=True)
    amount_salary_balance = fields.Monetary(string="Salary Balance", compute="_compute_amounts", store=True)
    amount_indirect_expense = fields.Monetary(string="Indirect Expenses", compute="_compute_amounts", store=True)
    amount_total = fields.Monetary(string="Total (All)", compute="_compute_amounts", store=True)
    amount_untaxed_total = fields.Monetary(string="SubTotal (All)", compute="_compute_amounts", store=True)
    last_odometer = fields.Float("Last Read")
    vehicle_odometer = fields.Float()
    current_odometer = fields.Float(string="Current Real", related="unit_id.odometer")
    notes = fields.Html()
    move_id = fields.Many2one(
        "account.move",
        "Journal Entry",
        readonly=True,
        help="Link to the automatically generated Journal Items.",
        ondelete="set null",
    )
    payment_state = fields.Selection(
        [
            ("not_paid", "Not Paid"),
            ("paid", "Paid"),
            ("partial", "Partially Paid"),
        ],
        readonly=True,
        compute="_compute_payment_information",
        store=True,
        tracking=True,
        help="It indicates the payment status of the expense.",
    )
    payment_move_ids = fields.Many2many(
        "account.move",
        string="Payment Entries",
        readonly=True,
        compute="_compute_payment_information",
        store=True,
    )
    payment_ids = fields.Many2many(
        "account.payment",
        readonly=True,
        compute="_compute_payment_information",
        store=True,
    )
    amount_residual = fields.Monetary(
        compute="_compute_payment_information",
        store=True,
        help="Remaining amount due.",
    )
    waybill_ids = fields.One2many("tms.waybill", "expense_id", string="Waybills", readonly=True)
    advance_ids = fields.One2many("tms.advance", "expense_id", string="Advances", readonly=True)
    fuel_qty_real = fields.Float(
        help="Fuel Qty computed based on Distance Real and Global Fuel "
        "Efficiency Real obtained by electronic reading and/or GPS"
    )
    fuel_diff = fields.Float(
        string="Fuel Difference",
        help="Fuel Qty Difference between Fuel Vouchers + Fuel Paid in Cash "
        "versus Fuel qty computed based on Distance Real and Global Fuel "
        "Efficiency Real obtained by electronic reading and/or GPS",
    )
    fuel_ids = fields.One2many("tms.fuel", "expense_id", string="Fuel Vouchers", readonly=True)
    fuel_efficiency = fields.Float(readonly=True, compute="_compute_fuel_efficiency")
    payment_move_id = fields.Many2one(
        "account.move",
        string="Payment Entry",
        readonly=True,
    )
    route_distance_loaded = fields.Float(
        compute="_compute_distances",
        store=True,
    )
    route_distance_empty = fields.Float(
        compute="_compute_distances",
        store=True,
    )
    distance_loaded = fields.Float(
        compute="_compute_distances",
        store=True,
    )
    distance_empty = fields.Float(
        compute="_compute_distances",
        store=True,
    )
    route_distance = fields.Float(
        compute="_compute_distances",
        string="Distance from routes",
        store=True,
    )
    distance = fields.Float(
        compute="_compute_distances",
        string="Distance Real",
        store=True,
        help="Route obtained by electronic reading and/or GPS",
    )
    income_km = fields.Monetary(
        compute="_compute_income_km",
        store=True,
    )
    expense_km = fields.Monetary(
        compute="_compute_expense_km",
        store=True,
    )
    percentage_km = fields.Float(
        "Productivity Percentage",
        compute="_compute_percentage_km",
        store=True,
    )
    fuel_efficiency_real = fields.Float()
    company_id = fields.Many2one(
        "res.company", string="Company", required=True, default=lambda self: self.env.user.company_id
    )
    analytic_account_id = fields.Many2one(
        "account.analytic.account",
        string="Analytic Account",
        check_company=True,
    )
    analytic_tag_ids = fields.Many2many(
        "account.analytic.tag",
        string="Analytic Tags",
        check_company=True,
    )

    @api.onchange("unit_id")
    def _onchange_unit_id(self):
        if self.unit_id:
            travels = self.env["tms.travel"].search([("unit_id", "=", self.unit_id.id), ("state", "=", "done")])
            return {"domain": {"driver_id": [("id", "in", travels.mapped("driver_id").ids)]}}

    @api.depends(
        "move_id.line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched",
        "move_id.line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual",
        "move_id.line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency",
        "move_id.line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched",
        "move_id.line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual",
        "move_id.line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency",
        "move_id.line_ids.debit",
        "move_id.line_ids.credit",
        "move_id.line_ids.currency_id",
        "move_id.line_ids.amount_currency",
        "move_id.line_ids.amount_residual",
        "move_id.line_ids.amount_residual_currency",
        "move_id.line_ids.payment_id.state",
        "move_id.line_ids.full_reconcile_id",
    )
    def _compute_payment_information(self):
        for rec in self:
            if not rec.move_id:
                rec.payment_state = False
                continue
            amount_residual = abs(
                sum(
                    rec.move_id.line_ids.filtered(
                        lambda line: line.account_id.user_type_id.type in ("receivable", "payable")
                        and line.partner_id == rec.driver_id.address_home_id
                    ).mapped("amount_residual")
                )
            )
            if float_compare(amount_residual, 0.0, precision_rounding=rec.currency_id.rounding) == 0:
                rec.payment_state = "paid"
            elif float_compare(amount_residual, rec.amount_salary_balance, precision_rounding=rec.currency_id.rounding) == 0:
                rec.payment_state = "not_paid"
            else:
                rec.payment_state = "partial"
            related_moves = rec.move_id.line_ids.mapped(
                "matched_debit_ids.debit_move_id.move_id"
            ) | rec.move_id.line_ids.mapped("matched_credit_ids.credit_move_id.move_id")
            rec.payment_move_ids = related_moves
            rec.payment_ids = related_moves.mapped("payment_id")
            rec.amount_residual = amount_residual

    @api.depends("company_id")
    def _compute_unit_ids(self):
        travels = self.env["tms.travel"].search([("state", "=", "done"), ("company_id", "=", self.company_id.id)])
        for rec in self:
            rec.unit_ids = travels.mapped("unit_id")

    @api.depends("travel_ids")
    def _compute_income_km(self):
        for rec in self:
            subtotal_waybills = sum(rec.mapped("travel_ids.waybill_ids.amount_untaxed"))
            try:
                rec.income_km = subtotal_waybills / rec.distance
            except ZeroDivisionError:
                rec.income_km = 0.0

    @api.depends("distance", "amount_total_driver_expenses", "amount_real_expense")
    def _compute_expense_km(self):
        for rec in self:
            try:
                rec.expense_km = (rec.amount_total_driver_expenses + rec.amount_real_expense) / rec.distance
            except ZeroDivisionError:
                rec.expense_km = 0.0

    @api.depends("income_km", "expense_km")
    def _compute_percentage_km(self):
        for rec in self:
            try:
                rec.percentage_km = rec.income_km / rec.expense_km
            except ZeroDivisionError:
                rec.percentage_km = 0.0

    @api.depends("fuel_qty", "distance")
    def _compute_fuel_efficiency(self):
        for rec in self:
            fuel_efficiency = 0
            if rec.distance and rec.fuel_qty:
                fuel_efficiency = rec.distance / rec.fuel_qty
            rec.fuel_efficiency = fuel_efficiency

    @api.depends(
        "expense_line_ids",
        "travel_ids",
        "expense_line_ids.price_unit",
        "expense_line_ids.product_qty",
        "expense_line_ids.tax_ids",
        "expense_line_ids.product_id",
    )
    def _compute_amounts(self):
        for rec in self:
            amount_salary = sum(
                rec.expense_line_ids.filtered(lambda l: l.line_type == "salary").mapped("amount_total")
            )
            amount_other_income = sum(
                rec.expense_line_ids.filtered(lambda l: l.line_type == "other_income").mapped("amount_total")
            )
            amount_salary_discount = sum(
                rec.expense_line_ids.filtered(lambda l: l.line_type == "salary_discount").mapped("amount_total")
            )
            amount_salary_retention = sum(
                rec.expense_line_ids.filtered(lambda l: l.line_type == "salary_retention").mapped("amount_total")
            )
            amount_total_driver_expenses = (
                amount_salary + amount_other_income + amount_salary_discount + amount_salary_retention
            )
            amount_real_expense = sum(
                rec.expense_line_ids.filtered(lambda l: l.line_type == "real_expense").mapped("amount_untaxed")
            )
            amount_tax_real = sum(
                rec.expense_line_ids.filtered(lambda l: l.line_type == "real_expense").mapped("tax_amount")
            )
            amount_total_real = amount_real_expense + amount_tax_real
            amount_advance = sum(rec.mapped("travel_ids.advance_ids.amount"))
            amount_advance_expense_balance = amount_total_real - amount_advance
            amount_salary_balance = amount_total_driver_expenses + amount_advance_expense_balance
            amount_fuel = sum(rec.expense_line_ids.filtered(lambda l: l.line_type == "fuel").mapped("amount_total"))
            amount_tax_fuel = sum(rec.expense_line_ids.filtered(lambda l: l.line_type == "fuel").mapped("tax_amount"))
            amount_total_fuel = amount_fuel + amount_tax_fuel
            amount_indirect_expense = sum(
                rec.expense_line_ids.filtered(lambda l: l.line_type == "indirect_expense").mapped("amount_total")
            )
            amount_total = (
                amount_total_driver_expenses + amount_total_real + amount_total_fuel + amount_indirect_expense
            )

            fuel_qty = sum(rec.expense_line_ids.filtered(lambda l: l.line_type == "fuel").mapped("product_qty"))
            rec.update(
                {
                    "amount_salary": amount_salary,
                    "amount_other_income": amount_other_income,
                    "amount_salary_discount": amount_salary_discount,
                    "amount_salary_retention": amount_salary_retention,
                    "amount_total_driver_expenses": amount_total_driver_expenses,
                    "amount_real_expense": amount_real_expense,
                    "amount_tax_real": amount_tax_real,
                    "amount_total_real": amount_total_real,
                    "amount_advance": amount_advance,
                    "amount_advance_expense_balance": amount_advance_expense_balance,
                    "amount_salary_balance": amount_salary_balance,
                    "amount_fuel": amount_fuel,
                    "amount_tax_fuel": amount_tax_fuel,
                    "amount_total_fuel": amount_total_fuel,
                    "amount_indirect_expense": amount_indirect_expense,
                    "amount_total": amount_total,
                    "fuel_qty": fuel_qty,
                }
            )

    @api.depends("travel_ids")
    def _compute_distances(self):
        for rec in self:
            rec.update(
                {
                    "route_distance_empty": sum(rec.travel_ids.mapped("route_distance_empty")),
                    "route_distance_loaded": sum(rec.travel_ids.mapped("route_distance_loaded")),
                    "route_distance": sum(rec.travel_ids.mapped("route_distance")),
                    "distance_empty": sum(rec.travel_ids.mapped("distance_empty")),
                    "distance_loaded": sum(rec.travel_ids.mapped("distance_loaded")),
                    "distance": sum(rec.travel_ids.mapped("distance")),
                }
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = self.env["ir.sequence"].next_by_code("tms.expense") or _("New")
        return super().create(vals_list)

    def unlink(self):
        if self.filtered(lambda rec: rec.state != "draft"):
            raise UserError(_("You can only delete expenses in draft state."))
        for rec in self:
            travels = self.env["tms.travel"].search([("expense_id", "=", rec.id)])
            travels.write({"expense_id": False, "state": "done"})
            advances = self.env["tms.advance"].search([("expense_id", "=", rec.id)])
            advances.write({"expense_id": False, "state": "confirmed"})
            fuel_logs = self.env["tms.fuel"].search([("expense_id", "=", rec.id)])
            fuel_logs.write({"expense_id": False, "state": "confirmed"})
            return super().unlink()

    def action_draft(self):
        for rec in self:
            rec.state = "draft"

    def action_register_payment(self):
        if any(advance.payment_state == "paid" for advance in self):
            raise UserError(_("At least one of the selected expenses is already paid."))
        return {
            "name": _("Register Payment"),
            "res_model": "account.payment.register",
            "view_mode": "form",
            "context": {
                "active_model": "tms.expense",
                "active_ids": self.ids,
                "dont_redirect_to_payments": True,
            },
            "target": "new",
            "type": "ir.actions.act_window",
        }

    def action_open_related_moves(self):
        self.ensure_one()
        moves = self.payment_move_ids | self.move_id
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_journal_line")
        if len(moves) > 1:
            action["domain"] = [("id", "in", moves.ids)]
        elif len(moves) == 1:
            form_view = [(self.env.ref("account.view_move_form").id, "form")]
            if "views" in action:
                action["views"] = form_view + [(state, view) for state, view in action["views"] if view != "form"]
            else:
                action["views"] = form_view
            action["res_id"] = moves.id
        else:
            action = {"type": "ir.actions.act_window_close"}

        action["context"] = {
            "no_create": True,
            "no_edit": True,
        }
        return action

    def action_open_payments(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_account_payments_payable")
        if len(self.payment_ids) > 1:
            action["domain"] = [("id", "in", self.payment_ids.ids)]
        elif len(self.payment_ids) == 1:
            form_view = [(self.env.ref("account.view_account_payment_form").id, "form")]
            if "views" in action:
                action["views"] = form_view + [(state, view) for state, view in action["views"] if view != "form"]
            else:
                action["views"] = form_view
            action["res_id"] = self.payment_ids.id
        else:
            action = {"type": "ir.actions.act_window_close"}

        action["context"] = {
            "no_create": True,
            "no_edit": True,
        }
        return action

    @api.model
    def prepare_move_line(self, name, ref, account_id, debit, credit, journal_id, partner_id):
        return (
            0,
            0,
            {
                "name": name,
                "ref": ref,
                "account_id": account_id,
                "debit": debit,
                "credit": credit,
                "journal_id": journal_id,
                "partner_id": partner_id,
                "company_id": self.env.user.company_id.id,
            },
        )

    @api.model
    def _create_fuel_vouchers(self, line):
        return self.env["tms.fuel"].create(
            {
                "travel_id": line.travel_id.id,
                "product_id": line.product_id.id,
                "price_unit": line.price_unit,
                "amount_untaxed": line.amount_untaxed,
                "partner_id": line.partner_id.id,
                "product_qty": line.product_qty,
                "product_uom_id": line.product_uom_id.id,
                "tax_amount": line.tax_amount,
                "state": "closed",
                "date": line.date,
                "expense_id": line.expense_id.id,
                "ref": line.ref,
                "created_from_expense": True,
                "expense_line_id": line.id,
            }
        )

    def higher_than_zero_move(self):
        for rec in self:
            move_lines = []
            invoices = []
            move_obj = rec.env["account.move"]
            journal_id = rec._get_expense_journal()
            advance_account_id = (
                rec.driver_id.property_tms_advance_account_id.id or rec.company_id.advance_account_id.id
            )
            negative_account = (
                rec.driver_id.property_tms_expense_negative_account_id.id
                or rec.company_id.expense_negative_account_id.id
            )
            driver_account_payable = rec.driver_id.address_home_id.property_account_payable_id.id
            # We check if the advance amount is higher than zero to create
            # a move line
            if rec.amount_advance > 0:
                move_line = rec.prepare_move_line(
                    _("Advance Discount"),
                    rec.name,
                    advance_account_id,
                    0.0,
                    rec.amount_advance,
                    journal_id,
                    rec.driver_id.address_home_id.id,
                )
                move_lines.append(move_line)
            return {
                "move_lines": move_lines,
                "invoices": invoices,
                "move_obj": move_obj,
                "journal_id": journal_id,
                "advance_account_id": advance_account_id,
                "negative_account": negative_account,
                "driver_account_payable": driver_account_payable,
            }

    def check_expenseline_invoice(self, line, result, product_account):
        for rec in self:
            # We check if the expense line is an invoice to create it
            # and make the move line based in the total with taxes
            inv_id = False
            if line.is_invoice:
                inv_id = rec.create_supplier_invoice(line)
                inv_id.action_post()
                result["invoices"].append(inv_id)
                move_line = rec.prepare_move_line(
                    (rec.name + " " + line.name + " - Inv ID - " + str(inv_id.id)),
                    (rec.name + " - Inv ID - " + str(inv_id.id)),
                    (line.partner_id.property_account_payable_id.id),
                    (line.amount_total if line.amount_total > 0.0 else 0.0),
                    (line.amount_total if line.amount_total <= 0.0 else 0.0),
                    result["journal_id"],
                    line.partner_id.id,
                )
            else:
                move_line = rec.prepare_move_line(
                    rec.name + " " + line.name,
                    rec.name,
                    product_account,
                    (line.amount_untaxed if line.amount_untaxed > 0.0 else 0.0),
                    (line.amount_untaxed * -1.0 if line.amount_untaxed < 0.0 else 0.0),
                    result["journal_id"],
                    rec.driver_id.address_home_id.id,
                )
            result["move_lines"].append(move_line)
            if line.is_invoice:
                continue
            # we check the line tax to create the move line if
            # the line not be an invoice
            # TODO: Fix this, this only works when the expense has 1 tax
            taxes = line.tax_ids.compute_all(price_unit=line.amount_untaxed, currency=rec.currency_id)["taxes"]
            for tax in taxes:
                tax_account = tax["account_id"]
                tax_amount = line.tax_amount
                # We create a move line for the line tax
                move_line = rec.prepare_move_line(
                    _("Tax Line: %(name)s %(line)s", name=rec.name, line=line.name),
                    rec.name,
                    tax_account,
                    (tax_amount if tax_amount > 0.0 else 0.0),
                    (tax_amount if tax_amount <= 0.0 else 0.0),
                    result["journal_id"],
                    rec.driver_id.address_home_id.id,
                )
                result["move_lines"].append(move_line)

    def create_expense_line_move_line(self, line, result):
        for rec in self:
            # We only need all the lines except the fuel and the
            # made up expenses
            if line.line_type == "fuel" and (not line.control or line.expense_fuel_log):
                rec.create_fuel_vouchers(line)
            if line.line_type not in ("fuel"):
                product_account = (
                    result["negative_account"]
                    if (line.product_id.tms_product_category == "negative_balance")
                    else (line.product_id.property_account_expense_id.id)
                    if (line.product_id.property_account_expense_id.id)
                    else (line.product_id.categ_id.property_account_expense_categ_id.id)
                    if (line.product_id.categ_id.property_account_expense_categ_id.id)
                    else False
                )
                if not product_account:
                    raise UserError(
                        _(
                            "Warning ! Expense Account is not defined for product %(product)s",
                            product=line.product_id.name,
                        )
                    )
                self.check_expenseline_invoice(line, result, product_account)

    def check_balance_value(self, result):
        for rec in self:
            balance = rec.amount_salary_balance
            if balance < 0:
                move_line = rec.prepare_move_line(
                    _("Negative Balance"),
                    rec.name,
                    result["negative_account"],
                    balance * -1.0,
                    0.0,
                    result["journal_id"],
                    rec.driver_id.address_home_id.id,
                )
            else:
                move_line = rec.prepare_move_line(
                    rec.name,
                    rec.name,
                    result["driver_account_payable"],
                    0.0,
                    balance,
                    result["journal_id"],
                    rec.driver_id.address_home_id.id,
                )
            result["move_lines"].append(move_line)

    def reconcile_account_move(self, result):
        for rec in self:
            move = {
                "date": fields.Date.today(),
                "journal_id": result["journal_id"],
                "name": rec.name,
                "line_ids": result["move_lines"],
                "company_id": self.env.user.company_id.id,
            }
            move_id = result["move_obj"].create(move)
            if not move_id:
                raise UserError(_("An error has occurred in the creation of the accounting move. "))
            move_id.action_post()
            # Here we reconcile the invoices with the corresponding
            # move line
            rec.reconcile_supplier_invoices(result["invoices"], move_id)
            rec.write({"move_id": move_id.id, "state": "confirmed"})

    # def action_confirm(self):
    #     for rec in self:
    #         if rec.move_id or rec.state == "confirmed":
    #             raise UserError(_("You can not confirm a confirmed expense."))
    #         rec.get_travel_info()
    #         result = rec.higher_than_zero_move()
    #         for line in rec.expense_line_ids:
    #             rec.create_expense_line_move_line(line, result)
    #         # Here we check if the balance is positive or negative to create
    #         # the move line with the correct values
    #         rec.check_balance_value(result)
    #         rec.reconcile_account_move(result)

    def action_confirm(self):
        for rec in self:
            if rec.move_id or rec.state == "confirmed":
                raise UserError(_("You can not confirm a confirmed expense."))
            rec.get_travel_info()
            rec._compute_amounts()
            move_vals = rec._prepare_move_vals()
            move = self.env["account.move"].create(move_vals)
            move.action_post()
            rec.write({"move_id": move.id, "state": "confirmed"})
            rec._reconcile_supplier_invoices()

    def _reconcile_supplier_invoices(self):
        self.ensure_one()
        for line in self.expense_line_ids.filtered(lambda l: l.is_invoice):
            move_line = self.move_id.line_ids.filtered(lambda l: l.expense_line_id == line)
            lines_to_reconcile = line.move_id.line_ids.filtered(lambda l: l.account_id == move_line.account_id)
            lines_to_reconcile |= move_line
            lines_to_reconcile.reconcile()

    def _prepare_move_vals(self):
        self.ensure_one()
        move_vals = {
            "date": self.date,
            "journal_id": self._get_expense_journal(),
            "move_type": "entry",
            "ref": self.name,
            "line_ids": self._prepare_move_line_vals(),
            "company_id": self.company_id.id,
        }
        return move_vals

    def _prepare_move_line_vals(self):
        self.ensure_one()
        move_line_vals = []
        for line in self.expense_line_ids:
            if line.line_type == "fuel" and not line.control:
                self._create_fuel_vouchers(line)
            elif line.is_invoice:
                invoice = self._create_supplier_invoice(line)
                move_line_vals.extend(self._prepare_move_line(line, invoice))
            elif line.line_type != "fuel":
                move_line_vals.extend(self._prepare_move_line(line))
        if self.amount_salary_balance:
            move_line_vals.extend(self._prepare_move_line(line_type="balance"))
        if self.amount_advance:
            move_line_vals.extend(self._prepare_move_line(line_type="advance"))
        return move_line_vals

    def _prepare_move_line(self, line=False, invoice=False, line_type=False):
        self.ensure_one()
        move_line_vals = []
        if line:
            name = line.name
            account_id = line.product_id.product_tmpl_id._get_product_accounts()["expense"].id
            partner_id = line.partner_id.id if line.partner_id else line.expense_id.driver_id.address_home_id.id
            debit = line.amount_total if line.amount_total > 0 else 0.0
            credit = line.amount_total * -1 if line.amount_total < 0 else 0.0
            analytic_account_id = line.analytic_account_id.id
            analytic_tag_ids = [(6, 0, line.analytic_tag_ids.ids)]
        if line and invoice:
            account_id = line.partner_id.property_account_payable_id.id
            partner_id = invoice.partner_id.id
        if line_type == "advance":
            name = _("Expense %(name)s - Advance", name=self.name)
            account_id = self.company_id.advance_account_id.id
            partner_id = self.driver_id.address_home_id.id
            debit = self.amount_advance * -1 if self.amount_advance < 0 else 0.0
            credit = self.amount_advance if self.amount_advance > 0 else 0.0
            analytic_account_id = self.analytic_account_id.id
            analytic_tag_ids = [(6, 0, self.analytic_tag_ids.ids)]
        if line_type == "balance" and self.amount_salary_balance:
            name = _("Expense %(name)s - Salary Balance", name=self.name)
            account_id = self.driver_id.address_home_id.property_account_payable_id.id
            if self.amount_salary_balance < 0:
                account_id = self.company_id.expense_negative_account_id.id
            partner_id = self.driver_id.address_home_id.id
            debit = self.amount_salary_balance * -1 if self.amount_salary_balance < 0 else 0.0
            credit = self.amount_salary_balance if self.amount_salary_balance > 0 else 0.0
            analytic_account_id = self.analytic_account_id.id
            analytic_tag_ids = [(6, 0, self.analytic_tag_ids.ids)]
        move_line_vals.append(
            (
                0,
                0,
                {
                    "name": name,
                    "account_id": account_id,
                    "partner_id": partner_id,
                    "debit": debit,
                    "credit": credit,
                    "analytic_account_id": analytic_account_id,
                    "analytic_tag_ids": analytic_tag_ids,
                    "expense_line_id": line.id if line else False,
                },
            )
        )
        return move_line_vals

    def action_cancel(self):
        self.ensure_one()
        if self.payment_state != "not_paid":
            raise UserError(_("You cannot cancel an expense that is paid."))
        if self.state == "confirmed":
            self.move_id.line_ids.remove_move_reconcile()
            self.move_id.button_cancel()
            self.move_id.unlink()
            self.fuel_ids.filtered(lambda x: x.created_from_expense).unlink()
            invoices = self.expense_line_ids.filtered(lambda x: not x.control).mapped("move_id")
            invoices.line_ids.remove_move_reconcile()
            invoices.button_cancel()
            invoices.unlink()
        self.write(
            {
                "state": "cancel",
            }
        )

    def _unattach_info(self):
        for rec in self:
            rec.expense_line_ids.filtered(lambda l: l.control or l.travel_id not in rec.travel_ids).unlink()
            travels = self.env["tms.travel"].search([("expense_id", "=", rec.id)])
            travels.write({"expense_id": False, "state": "done"})
            advances = self.env["tms.advance"].search([("expense_id", "=", rec.id)])
            advances.write({"expense_id": False, "state": "confirmed"})
            fuel_logs = self.env["tms.fuel"].search(
                [("expense_id", "=", rec.id), ("created_from_expense", "=", False)]
            )
            fuel_logs.write({"expense_id": False, "state": "confirmed"})
            waybills = self.env["tms.waybill"].search([("expense_id", "=", rec.id)])
            waybills.write({"expense_id": False, "state": "confirmed"})

    def _get_advance_lines(self, advance):
        if advance.auto_expense and advance.state != "cancel":
            return [
                (
                    0,
                    0,
                    {
                        "name": _("Advance: %(name)s", name=advance.name),
                        "travel_id": advance.travel_id.id,
                        "expense_id": self.id,
                        "line_type": "real_expense",
                        "product_id": advance.product_id.id,
                        "product_qty": 1.0,
                        "price_unit": advance.amount,
                        "control": True,
                    },
                )
            ]
        return []

    @api.model
    def _get_fuel_lines(self, fuel):
        return [
            (
                0,
                0,
                {
                    "name": _("Fuel voucher: %(name)s", name=fuel.name),
                    "travel_id": fuel.travel_id.id,
                    "line_type": "fuel",
                    "product_id": fuel.product_id.id,
                    "product_qty": fuel.product_qty,
                    "product_uom_id": fuel.product_id.uom_id.id,
                    "price_unit": fuel.price_unit,
                    "tax_ids": [(6, 0, fuel.tax_ids.ids)],
                    "is_invoice": bool(fuel.move_id),
                    "move_id": fuel.move_id.id,
                    "control": True,
                    "partner_id": fuel.partner_id.id,
                    "date": fuel.date,
                    "ref": fuel.ref,
                },
            )
        ]

    def _get_salary_lines(self, travel):
        for rec in self:
            product_id = self.env["product.product"].search([("tms_product_category", "=", "salary")])
            if not product_id:
                raise UserError(
                    _("You must create a product for the driver salary with the Salary TMS Product Category")
                )
            return [
                (
                    0,
                    0,
                    {
                        "name": _("Salary for travel: ") + str(travel.name),
                        "travel_id": travel.id,
                        "expense_id": rec.id,
                        "line_type": "salary",
                        "product_qty": 1.0,
                        "product_uom_id": product_id.uom_id.id,
                        "product_id": product_id.id,
                        "price_unit": rec._get_driver_salary(travel),
                        "control": True,
                    },
                )
            ]

    @api.model
    def _get_driver_salary(self, travel):
        waybills = travel.waybill_ids.filtered(lambda r: r.state != "cancel")
        price_values = travel.mapped("route_id.driver_factor_ids")._get_amount_and_qty(
            distance=travel.route_distance,
            distance_real=travel.distance,
            weight=sum(waybills.mapped("product_weight")),
            volume=sum(waybills.mapped("product_volume")),
            income=sum(
                waybills.mapped("waybill_line_ids")
                .filtered(lambda r: r.product_id.apply_for_salary)
                .mapped("amount_untaxed")
            ),
        )
        return price_values["fixed_amount"] + (price_values["amount"] * price_values["quantity"])

    def _validate_records_for_expense(self):
        self.ensure_one()
        errors = []
        advances = self.travel_ids.mapped("advance_ids").filtered(
            lambda a: a.state not in ["confirmed", "cancel"] or a.payment_state != "paid"
        )
        if advances:
            errors.append(
                _(
                    "All the advances must be confirmed or cancelled and paid.\nAdvances with error:\n%(advances)s\n",
                    advances="\n".join(advances.mapped("name")),
                )
            )
        fuels = self.travel_ids.mapped("fuel_ids").filtered(lambda f: f.state != "confirmed")
        if fuels:
            errors.append(
                _(
                    "All the fuel vouchers must be confirmed.\nFuel vourchers with error:\n%(fuels)s",
                    fuels="\n".join(fuels.mapped("name")),
                )
            )
        waybills = self.travel_ids.mapped("waybill_ids").filtered(lambda w: w.state != "confirmed")
        if waybills:
            errors.append(
                _(
                    "All the waybills must be confirmed.\nWaybills with error:\n%(waybills)s",
                    waybills="\n".join(waybills.mapped("name")),
                )
            )
        if any(x.tax_ids and not x.is_invoice for x in self.expense_line_ids):
            errors.append(
                _(
                    "If you have taxes, you must have an invoice.\nLines with this issue:\n%(lines)s",
                    lines="\n".join(
                        self.waybill_line_ids.filtered(lambda l: l.tax_ids and not l.is_invoice).mapped("name")
                    ),
                )
            )
        if errors:
            raise UserError("\n".join(errors))

    def get_travel_info(self):
        for rec in self:
            rec._unattach_info()
            rec._validate_records_for_expense()
            rec.travel_ids.write({"state": "closed", "expense_id": rec.id})
            rec.travel_ids.mapped("fuel_ids").filtered(lambda f: f.state == "confirmed").write(
                {"state": "closed", "expense_id": rec.id}
            )
            rec.travel_ids.mapped("advance_ids").filtered(lambda f: f.state == "confirmed").write(
                {"state": "closed", "expense_id": rec.id}
            )
            rec.travel_ids.mapped("waybill_ids").filtered(lambda f: f.state == "confirmed").write(
                {"state": "closed", "expense_id": rec.id}
            )
            lines_to_create = []
            for travel in rec.travel_ids:
                for advance in travel.advance_ids:
                    lines_to_create.extend(rec._get_advance_lines(advance))
                for fuel in travel.fuel_ids:
                    lines_to_create.extend(rec._get_fuel_lines(fuel))
                lines_to_create.extend(rec._get_salary_lines(travel))
            rec.write({"expense_line_ids": lines_to_create})
            rec._compute_amounts()

    def _get_expense_journal(self):
        return self.company_id.expense_journal_id.id

    def _prepare_supplier_invoice_line(self, line):
        return [(0, 0, self._prepare_supplier_invoice_line_vals(line))]

    def _prepare_supplier_invoice_line_vals(self, line):
        fpos = line.partner_id.property_account_position_id
        product_account = line.product_id.product_tmpl_id.get_product_accounts(fpos)["expense"]
        return {
            "name": line.name,
            "product_id": line.product_id.id,
            "quantity": line.product_qty,
            "price_unit": line.price_unit,
            "account_id": product_account,
            "product_uom_id": line.product_uom_id.id,
            "analytic_tag_ids": [(6, 0, line.analytic_tag_ids.ids)],
            "analytic_account_id": line.analytic_account_id.id,
            "tax_ids": [(6, 0, line.tax_ids.ids)],
        }

    def _prepare_supplier_invoice(self, line):
        return {
            "partner_id": line.partner_id.id,
            "ref": line.ref,
            "invoice_origin": line.expense_id.name,
            "company_id": line.expense_id.company_id.id,
            "move_type": "in_invoice",
            "invoice_line_ids": self._prepare_supplier_invoice_line(line),
            "currency_id": line.currency_id.id,
            "invoice_date": line.date,
            "fiscal_position_id": line.partner_id.property_account_position_id.id,
        }

    def _create_supplier_invoice(self, line):
        move = (
            self.env["account.move"]
            .with_context(default_move_type="in_invoice")
            .create(self._prepare_supplier_invoice(line))
        )
        move.action_post()
        line.write({"move_id": move.id})
        return move

    def reconcile_supplier_invoices(self, move_ids, move_id):
        move_line_obj = self.env["account.move.line"]
        for invoice in move_ids:
            moves = self.env["account.move.line"]
            invoice_str_id = str(invoice.id)
            expense_move_line = move_line_obj.search([("move_id", "=", move_id.id), ("name", "ilike", invoice_str_id)])
            if not expense_move_line:
                raise UserError(_("Error ! Move line was not found, please check your data."))
            moves |= expense_move_line
            moves |= invoice.line_ids.filtered(
                lambda x: x.account_id.reconcile and x.account_id.user_type_id.id in [2]
            )
            moves.reconcile()
        return True


class TmsExpenseLine(models.Model):
    _name = "tms.expense.line"
    _description = "Expense Line"
    _order = "line_type desc, name asc"

    travel_id = fields.Many2one("tms.travel", ondelete="restrict")
    travel_ids = fields.Many2many("tms.travel", string="Travels", readonly=True, compute="_compute_travel_ids")
    expense_id = fields.Many2one("tms.expense", ondelete="cascade", readonly=True)
    product_qty = fields.Float(string="Qty", default=1.0)
    currency_id = fields.Many2one(related="expense_id.currency_id", store=True)
    price_unit = fields.Monetary()
    amount_untaxed = fields.Monetary(
        compute="_compute_amount_untaxed",
        string="Subtotal",
        store=True,
    )
    product_uom_id = fields.Many2one("uom.uom", string="Unit of Measure")
    line_type = fields.Selection(
        related="product_id.tms_product_category",
        store=True,
    )
    name = fields.Char("Description", required=True)
    sequence = fields.Integer(default=10)
    amount_total = fields.Monetary(
        string="Total",
        compute="_compute_amounts",
    )
    tax_amount = fields.Monetary(
        compute="_compute_amounts",
    )
    tax_ids = fields.Many2many("account.tax", string="Taxes", domain=[("type_tax_use", "=", "purchase")])
    notes = fields.Text()
    date = fields.Date()
    control = fields.Boolean()
    automatic = fields.Boolean(
        help="Check this if you want to create Advances and/or Fuel Vouchers for this line automatically"
    )
    is_invoice = fields.Boolean(string="Is Invoice?")
    partner_id = fields.Many2one(
        "res.partner",
        string="Supplier",
    )
    invoice_date = fields.Date()
    ref = fields.Char()
    move_id = fields.Many2one("account.move", string="Supplier Invoice", ondelete="set null")
    product_id = fields.Many2one(
        "product.product",
        string="Product",
        required=True,
    )
    company_id = fields.Many2one(
        related="expense_id.company_id",
        store=True,
    )
    analytic_account_id = fields.Many2one(
        "account.analytic.account",
        string="Analytic Account",
        check_company=True,
    )
    analytic_tag_ids = fields.Many2many(
        "account.analytic.tag",
        string="Analytic Tags",
        check_company=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self._context.get("default_expense_id"):
            expense = self.env["tms.expense"].browse(self._context["default_expense_id"])
            res.update({"travel_id": expense.travel_ids if len(expense.travel_ids) == 1 else False})
        return res

    @api.onchange("product_id")
    def _onchange_product_id(self):
        self.update(
            {
                "tax_ids": [(6, 0, self.product_id.supplier_taxes_id.ids)],
                "product_uom_id": self.product_id.uom_id.id,
                "name": self.product_id.name,
            }
        )

    @api.onchange("tax_ids")
    def _onchange_tax_ids(self):
        self.update(
            {
                "is_invoice": True if self.tax_ids else False,
            }
        )

    def _get_discount_categories(self):
        return ["salary_retention", "salary_discount"]

    @api.depends("tax_ids", "product_qty", "price_unit", "line_type", "product_id")
    def _compute_amounts(self):
        for rec in self:
            taxes = rec.tax_ids.compute_all(
                price_unit=rec.price_unit,
                currency=rec.currency_id,
                quantity=rec.product_qty,
                partner=rec.expense_id.driver_id.sudo().address_home_id,
            )
            discount_categories = self._get_discount_categories()
            multiplicator = -1 if rec.line_type in discount_categories else 1
            rec.update(
                {
                    "tax_amount": sum(t.get("amount", 0.0) for t in taxes.get("taxes", [])) * multiplicator,
                    "amount_untaxed": taxes["total_excluded"] * multiplicator,
                    "amount_total": taxes["total_included"] * multiplicator,
                }
            )

    @api.depends("expense_id.travel_ids")
    def _compute_travel_ids(self):
        for rec in self:
            rec.travel_ids = rec.expense_id.travel_ids

    @api.constrains("product_qty", "price_unit")
    def _check_amounts(self):
        for rec in self:
            if not rec.price_unit or not rec.product_qty:
                raise UserError(_("Total amount cannot be zero!"))
