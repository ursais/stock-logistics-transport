# Copyright 2021 Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

# List of tuples with the following format
# ('old.model.name', 'new.model.name'),
models_to_rename = [
    ("fleet.vehicle.log.fuel", "tms.fuel"),
]

# List of tuples with the following format
# ('old_table_name', 'new_table_name'),
tables_to_rename = [("fleet_vehicle_log_fuel", "tms_fuel")]

# List of tuples with the following format
# ('model.name', 'table_name', 'old_field', 'new_field'),
fields_to_rename = [
    ("tms.fuel", "tms_fuel", "vehicle_id", "unit_id"),
    ("tms.fuel", "tms_fuel", "employee_id", "driver_id"),
    ("tms.fuel", "tms_fuel", "price_total", "amount_total"),
    ("tms.fuel", "tms_fuel", "price_subtotal", "amount_untaxed"),
    ("tms.fuel", "tms_fuel", "invoice_id", "move_id"),
    ("tms.fuel", "tms_fuel", "vendor_id", "partner_id"),
    ("tms.fuel", "tms_fuel", "ticket_number", "ref"),
    ("hr.employee", "hr_employee", "tms_advance_account_id", "property_tms_advance_account_id"),
    ("hr.employee", "hr_employee", "tms_expense_negative_account_id", "property_tms_expense_negative_account_id"),
    ("tms.advance", "tms_advance", "employee_id", "driver_id"),
    ("tms.transportable", "tms_transportable", "uom_id", "product_uom_id"),
    ("tms.travel", "tms_travel", "employee_id", "driver_id"),
    ("tms.unit.kit", "tms_unit_kit", "employee_id", "driver_id"),
    ("tms.waybill.line", "tms_waybill_line", "unit_price", "price_unit"),
    ("tms.waybill.line", "tms_waybill_line", "price_subtotal", "amount_untaxed"),
    ("tms.waybill.line", "tms_waybill_line", "price_total", "amount_total"),
    ("tms.waybill.transportable.line", "tms_waybill_transportable_line", "transportable_uom_id", "product_uom_id"),
    ("tms.waybill", "tms_waybill", "date_order", "date"),
    ("tms.waybill", "tms_waybill", "partner_invoice_id", "invoice_partner_id"),
    ("tms.waybill", "tms_waybill", "invoice_id", "move_id"),
]

# List of strings with the XML IDs of the records to delete
records_to_remove = [
    "tms.expense_report",
    "tms.view_employee_tms_inherit_form",
    "tms.account_move_tms_form",
]


def _fix_relation_invoice_waybill(cr):
    openupgrade.logged_query(
        cr, "ALTER TABLE account_move_line ADD COLUMN waybill_line_id INTEGER;", skip_no_result=True
    )
    openupgrade.logged_query(
        cr,
        """
        UPDATE account_move_line aml
        SET waybill_line_id = subquery.id
        FROM (SELECT wl.id AS id, aml.move_id AS move_id
            FROM tms_waybill_line wl
            LEFT JOIN tms_waybill wb ON wl.waybill_id = wb.id
            LEFT JOIN account_move am ON am.id = wb.invoice_id
            LEFT JOIN account_move_line aml ON aml.move_id = am.id) AS subquery
        WHERE aml.move_id = subquery.move_id;
        """,
        skip_no_result=True,
    )


def _fix_m2m_travel_waybill(cr):
    openupgrade.logged_query(cr, "ALTER TABLE tms_waybill ADD COLUMN travel_id INTEGER;", skip_no_result=True)
    openupgrade.logged_query(
        cr,
        """
        UPDATE tms_waybill
        SET travel_id = subquery.tms_travel_id
        FROM (SELECT tms_travel_id, tms_waybill_id
            FROM tms_travel_tms_waybill_rel) AS subquery
        WHERE id = subquery.tms_waybill_id;
        """,
        skip_no_result=True,
    )


def _create_customer_factors_from_waybill(cr):
    openupgrade.logged_query(
        cr,
        """
        ALTER TABLE tms_factor
        ADD COLUMN partner_id INTEGER,
        ADD COLUMN customer_route_id INTEGER,
        ADD COLUMN departure_address_id INTEGER,
        ADD COLUMN arrival_address_id INTEGER;
        """,
        skip_no_result=True,
    )
    cr.execute(
        """
        SELECT DISTINCT
            factor.name AS name,
            route.id AS customer_route_id,
            'customer' AS category,
            factor.factor_type AS factor_type,
            factor.factor AS factor,
            factor.fixed_amount AS fixed_amount,
            waybill.partner_id AS partner_id,
            waybill.departure_address_id AS departure_address_id,
            waybill.arrival_address_id AS arrival_address_id
        FROM tms_waybill AS waybill
        INNER JOIN tms_factor AS factor ON factor.waybill_id = waybill.id
        INNER JOIN tms_travel AS travel ON travel.id = waybill.travel_id
        INNER JOIN tms_route AS route ON route.id = travel.route_id;
        """
    )
    values = cr.dictfetchall()
    data = [tuple(v.get(k) for k in values[0].keys()) for v in values]
    args_str = ",".join(["%s"] * len(data))
    sql = (
        """
        INSERT INTO tms_factor (
            name,
            customer_route_id,
            category,
            factor_type,
            factor,
            fixed_amount,
            partner_id,
            departure_address_id,
            arrival_address_id
        ) VALUES %s"""
        % args_str
    )
    query = cr.mogrify(sql, data)
    openupgrade.logged_query(cr, query, skip_no_result=True)


def _populate_product_uom_id_waybill_line(cr):
    openupgrade.logged_query(
        cr, "ALTER TABLE tms_waybill_line ADD COLUMN product_uom_id INTEGER;", skip_no_result=True
    )
    openupgrade.logged_query(
        cr,
        """
        UPDATE tms_waybill_line
        SET product_uom_id = subquery.id
        FROM (
            SELECT
                template.uom_id AS id,
                product.id AS product_id
            FROM tms_waybill_line
            LEFT JOIN product_product product ON product.id = tms_waybill_line.product_id
            LEFT JOIN product_template template ON template.id = product.product_tmpl_id
        ) AS subquery
        WHERE tms_waybill_line.product_id = subquery.product_id;
        """,
        skip_no_result=True,
    )


@openupgrade.migrate()
def migrate(env, installed_version):
    _fix_relation_invoice_waybill(env.cr)
    openupgrade.logged_query(env.cr, "ALTER TABLE tms_waybill DROP CONSTRAINT tms_waybill_operating_unit_id_fkey;")
    openupgrade.rename_models(env.cr, models_to_rename)
    openupgrade.rename_tables(env.cr, tables_to_rename)
    openupgrade.rename_fields(env, fields_to_rename)
    openupgrade.delete_records_safely_by_xml_id(env, records_to_remove)
    _fix_m2m_travel_waybill(env.cr)
    _create_customer_factors_from_waybill(env.cr)
    _populate_product_uom_id_waybill_line(env.cr)
