# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

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


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.load_data(env, "base", "20.0.1.3/noupdate_changes.xml")
    _res_partner_bank_computes(env)
