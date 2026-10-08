# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


def _attribute_exclusions(cr):
    legacy = openupgrade.get_legacy_name("attribute_exclusion")
    if not openupgrade.table_exists(cr, legacy):
        return
    openupgrade.logged_query(
        cr,
        f"""
        INSERT INTO product_template_attribute_excluded_value_ids_rel
            (product_template_attribute_value_id,
             excluded_product_template_attribute_value_id)
        SELECT legacy.value_id, legacy.excluded_value_id
        FROM {legacy} legacy
        JOIN product_template_attribute_value value ON value.id = legacy.value_id
        JOIN product_template_attribute_value excluded
            ON excluded.id = legacy.excluded_value_id
        ON CONFLICT DO NOTHING
        """,
    )


@openupgrade.migrate()
def migrate(env, version):
    _attribute_exclusions(env.cr)
