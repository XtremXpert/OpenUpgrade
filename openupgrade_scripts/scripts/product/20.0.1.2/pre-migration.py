# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

_renamed_fields = [
    ("product.supplierinfo", "product_supplierinfo", "product_uom_id", "uom_id"),
]

# website.base.unit (website_sale) became product.base.unit (product)
_base_unit_xmlids = [
    ("website_sale.group_show_uom_price", "product.group_show_uom_price"),
    ("website_sale.base_unit_action", "product.base_unit_action"),
]


def _pricelist_items(cr):
    """
    The 'percentage' rule (percent_price) became 'discount' (price_discount),
    and the 'formula' rule became 'discount' or 'markup' depending on the sign
    of its discount; the other formula fields are unchanged.
    """
    openupgrade.logged_query(
        cr,
        """
        UPDATE product_pricelist_item
        SET compute_price = 'discount', price_discount = COALESCE(percent_price, 0)
        WHERE compute_price = 'percentage'
        """,
    )
    openupgrade.logged_query(
        cr,
        """
        UPDATE product_pricelist_item
        SET compute_price = CASE
            WHEN COALESCE(price_discount, 0) < 0 THEN 'markup' ELSE 'discount'
        END
        WHERE compute_price = 'formula'
        """,
    )


def _base_unit(cr):
    if not openupgrade.table_exists(cr, "website_base_unit"):
        return
    openupgrade.rename_models(cr, [("website.base.unit", "product.base.unit")])
    openupgrade.rename_tables(cr, [("website_base_unit", "product_base_unit")])
    openupgrade.update_module_moved_models(
        cr, "product.base.unit", "website_sale", "product"
    )
    openupgrade.rename_xmlids(cr, _base_unit_xmlids)


def _keep_attribute_exclusions(cr):
    """
    product.template.attribute.exclusion is gone: the excluded values are now
    a many2many on the attribute value, filled in post-migration.
    """
    if not openupgrade.table_exists(cr, "product_template_attribute_exclusion"):
        return
    openupgrade.logged_query(
        cr,
        f"""
        CREATE TABLE {openupgrade.get_legacy_name("attribute_exclusion")} AS
        SELECT DISTINCT
            exclusion.product_template_attribute_value_id AS value_id,
            rel.product_template_attribute_value_id AS excluded_value_id
        FROM product_template_attribute_exclusion exclusion
        JOIN product_attr_exclusion_value_ids_rel rel
            ON rel.product_template_attribute_exclusion_id = exclusion.id
        WHERE exclusion.product_template_attribute_value_id IS NOT NULL
        """,
    )


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_fields(env, _renamed_fields)
    _pricelist_items(env.cr)
    _base_unit(env.cr)
    _keep_attribute_exclusions(env.cr)
