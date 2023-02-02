# Copyright 2021 Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


def _create_vehicle_insurance_policy(env):
    env.cr.execute(
        """
        SELECT
            insurance_policy AS name,
            insurance_supplier_id AS partner_id,
            id AS unit_id,
            insurance_expiration AS expiration_date,
            create_date AS emission_date
        FROM fleet_vehicle
        WHERE insurance_policy IS NOT NULL AND insurance_supplier_id IS NOT NULL
    """
    )
    values = env.cr.dictfetchall()
    policies = env["fleet.vehicle.insurance"].create(values)
    _logger.warning("%s insurance policies created.", len(policies))


def _create_driver_license(env):
    env.cr.execute(
        """
        SELECT
            driver_license AS name,
            license_type AS license_type,
            id AS employee_id,
            COALESCE(license_expiration, create_date) AS expiration_date,
            COALESCE(license_valid_from, create_date) AS emission_date
        FROM hr_employee
        WHERE driver_license IS NOT NULL;
    """
    )
    values = env.cr.dictfetchall()
    licenses = []
    for value in values:
        if value.get("name") in licenses:
            value["name"] = "%s (copy)" % value["name"]
        licenses.append(value.get("name"))
    licenses = env["hr.employee.driver.license"].create(values)
    _logger.warning("%s driver licenses created.", len(licenses))


@openupgrade.migrate()
def migrate(env, installed_version):
    _create_vehicle_insurance_policy(env)
    _create_driver_license(env)
