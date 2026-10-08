# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


def _variant_images(cr):
    """An image of a variant is now an image of the attribute values of that
    variant"""
    if not openupgrade.column_exists(cr, "product_image", "product_variant_id"):
        return
    openupgrade.logged_query(
        cr,
        """
        INSERT INTO product_image_attribute_value_rel
            (product_image_id, product_template_attribute_value_id)
        SELECT image.id, combination.product_template_attribute_value_id
        FROM product_image image
        JOIN product_variant_combination combination
            ON combination.product_product_id = image.product_variant_id
        ON CONFLICT DO NOTHING
        """,
    )
    openupgrade.logged_query(
        cr,
        """
        UPDATE product_image SET has_attribute_value = TRUE
        WHERE id IN (SELECT product_image_id FROM product_image_attribute_value_rel)
        """,
    )


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.load_data(env, "website_sale", "20.0.1.1/noupdate_changes.xml")
    _variant_images(env.cr)
