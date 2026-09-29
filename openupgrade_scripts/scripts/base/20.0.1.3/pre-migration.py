# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

# pylint: disable=odoo-addons-relative-import
from odoo.addons.openupgrade_scripts.apriori import merged_modules, renamed_modules

_renamed_fields = [
    ("res.partner.bank", "res_partner_bank", "acc_number", "account_number"),
    (
        "res.partner.bank",
        "res_partner_bank",
        "sanitized_acc_number",
        "sanitized_account_number",
    ),
    ("res.partner.bank", "res_partner_bank", "acc_holder_name", "holder_name"),
]

# The website model moved from the website module to base
_renamed_xmlids = [
    ("website.default_website", "base.default_website"),
    (
        "website.constraint_website_domain_unique",
        "base.constraint_website_domain_unique",
    ),
]

_added_fields = [
    # res.bank is gone, its data now lives on res.partner.bank
    ("bank_name", "res.partner.bank", "res_partner_bank", "char", False, "base"),
    ("bank_bic", "res.partner.bank", "res_partner_bank", "char", False, "base"),
    ("street", "res.partner.bank", "res_partner_bank", "char", False, "base"),
    ("street2", "res.partner.bank", "res_partner_bank", "char", False, "base"),
    ("zip", "res.partner.bank", "res_partner_bank", "char", False, "base"),
    ("city", "res.partner.bank", "res_partner_bank", "char", False, "base"),
    ("state_id", "res.partner.bank", "res_partner_bank", "many2one", False, "base"),
    ("country_id", "res.partner.bank", "res_partner_bank", "many2one", False, "base"),
    ("zip_applicability", "res.country", "res_country", "selection", False, "base"),
    ("user_agent", "res.device.log", "res_device_log", "char", False, "base"),
]


def _keep_legacy_access_tables(cr):
    """
    ir.model.access and ir.rule are replaced by ir.access. Keep a copy of the
    old records (with their xmlids and groups) so that base's end-migration
    script can convert the custom ones once every module has loaded its own
    ir.access records. The old xmlids are removed: otherwise loading
    ir.access.csv files reusing the same xmlids would clash with them.
    """
    for table in ("ir_model_access", "ir_rule", "rule_group_rel"):
        if not openupgrade.table_exists(cr, table):
            continue
        openupgrade.logged_query(
            cr,
            f"CREATE TABLE {openupgrade.get_legacy_name(table)} AS "
            f"SELECT * FROM {table}",
        )
    openupgrade.logged_query(
        cr,
        f"""
        CREATE TABLE {openupgrade.get_legacy_name("access_xmlids")} AS
        SELECT id, module, name, model, res_id, noupdate
        FROM ir_model_data
        WHERE model IN ('ir.model.access', 'ir.rule')
        """,
    )
    openupgrade.logged_query(
        cr,
        "DELETE FROM ir_model_data WHERE model IN ('ir.model.access', 'ir.rule')",
    )


def _website_moved_to_base(cr):
    if not openupgrade.table_exists(cr, "website"):
        return
    openupgrade.update_module_moved_models(cr, "website", "website", "base")
    openupgrade.rename_xmlids(cr, _renamed_xmlids)


def _fill_partner_bank_from_res_bank(cr):
    """
    res.bank is obsolete: bank_name and bank_bic are now stored on
    res.partner.bank, which also received the address fields of the bank.
    """
    openupgrade.logged_query(
        cr,
        """
        UPDATE res_partner_bank rpb
        SET bank_name = rb.name,
            bank_bic = rb.bic,
            street = rb.street,
            street2 = rb.street2,
            zip = rb.zip,
            city = rb.city,
            state_id = rb.state,
            country_id = rb.country
        FROM res_bank rb
        WHERE rpb.bank_id = rb.id
        """,
    )


def _res_country_zip_applicability(cr):
    """
    Boolean zip_required became the selection zip_applicability. Standard
    countries are fixed by noupdate_changes.xml in post-migration.
    """
    openupgrade.logged_query(
        cr,
        """
        UPDATE res_country
        SET zip_applicability = CASE
            WHEN zip_required THEN 'required' ELSE 'optional'
        END
        """,
    )


def _res_company_font(cr):
    openupgrade.logged_query(
        cr,
        "UPDATE res_company SET font = 'Noto_Sans_Mono' WHERE font = 'Fira_Mono'",
    )


def _column_type(cr, table, column):
    cr.execute(
        """
        SELECT data_type FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s
        """,
        (table, column),
    )
    row = cr.fetchone()
    return row and row[0]


def _ir_model_fields_index(cr):
    """
    Boolean ir.model.fields.index became a selection (btree, btree_not_null,
    trigram). The ORM would cast the boolean to 'true'/'false', so do it here.
    """
    if _column_type(cr, "ir_model_fields", "index") != "boolean":
        return
    openupgrade.logged_query(
        cr,
        """
        ALTER TABLE ir_model_fields
            ALTER COLUMN index DROP DEFAULT,
            ALTER COLUMN index TYPE varchar
                USING CASE WHEN index THEN 'btree' END
        """,
    )


def _ir_actions_client_params_store(cr):
    """
    params_store was a Binary field holding the repr() of the params dict as
    raw bytes; it is now a Text field with the same content.
    """
    if _column_type(cr, "ir_act_client", "params_store") != "bytea":
        return
    openupgrade.logged_query(
        cr,
        """
        ALTER TABLE ir_act_client
            ALTER COLUMN params_store TYPE text
                USING convert_from(params_store, 'UTF8')
        """,
    )


def _res_device_log(cr):
    """
    user_id is now a plain integer, user_agent replaces platform + browser,
    and several fields became required.
    """
    openupgrade.lift_constraints(cr, "res_device_log", "user_id")
    openupgrade.logged_query(cr, "DELETE FROM res_device_log WHERE user_id IS NULL")
    openupgrade.logged_query(
        cr,
        """
        UPDATE res_device_log
        SET user_agent = COALESCE(
                NULLIF(TRIM(CONCAT_WS(' ', platform, browser)), ''), 'unknown'
            ),
            ip_address = COALESCE(ip_address, ''),
            first_activity = COALESCE(
                first_activity, last_activity, create_date, now() AT TIME ZONE 'UTC'
            ),
            last_activity = COALESCE(
                last_activity, first_activity, write_date, now() AT TIME ZONE 'UTC'
            )
        """,
    )


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        f"""
        CREATE TABLE {
            openupgrade.get_legacy_name("ir_module_module")
        } AS (SELECT name, state FROM ir_module_module);
        """,
    )
    openupgrade.update_module_names(
        env.cr, renamed_modules.items(), environment_namespec=True
    )
    openupgrade.update_module_names(
        env.cr, merged_modules.items(), merge_modules=True, environment_namespec=True
    )
    openupgrade.clean_transient_models(env.cr)
    _keep_legacy_access_tables(env.cr)
    _website_moved_to_base(env.cr)
    openupgrade.rename_fields(env, _renamed_fields)
    openupgrade.add_fields(env, _added_fields)
    _fill_partner_bank_from_res_bank(env.cr)
    _res_country_zip_applicability(env.cr)
    _res_company_font(env.cr)
    _ir_model_fields_index(env.cr)
    _ir_actions_client_params_store(env.cr)
    _res_device_log(env.cr)
