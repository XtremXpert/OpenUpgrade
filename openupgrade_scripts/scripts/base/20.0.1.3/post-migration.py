# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import importlib.util
import os

from openupgradelib import openupgrade


def _res_partner_bank_computes(env):
    """
    country_id was added in pre-migration (filled from the obsolete res.bank),
    so the ORM did not compute it for the other records; clearing_label_id
    (required) depends on it and holder_name has to be filled when the old
    acc_holder_name was empty.
    """
    banks = env["res.partner.bank"].with_context(active_test=False).search([])
    banks.filtered(lambda bank: not bank.country_id)._compute_country_id()
    banks.filtered(lambda bank: not bank.clearing_label_id)._compute_clearing_label_id()
    banks.filtered(lambda bank: not bank.holder_name)._compute_account_holder_name()
    env.flush_all()
    # the ORM could not set the constraint while the column was empty
    openupgrade.logged_query(
        env.cr,
        "ALTER TABLE res_partner_bank ALTER COLUMN clearing_label_id SET NOT NULL",
    )


def _access_conversion():
    path = os.path.join(os.path.dirname(__file__), "access_conversion.py")
    spec = importlib.util.spec_from_file_location("access_conversion", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.load_data(env, "base", "20.0.1.3/noupdate_changes.xml")
    _res_partner_bank_computes(env)
    # custom access rights and rules -> ir.access (see access_conversion.py)
    _access_conversion().convert(env)
