from odoo.tests import TransactionCase

from odoo.addons.openupgrade_framework import openupgrade_test


@openupgrade_test
class TestProductMigration(TransactionCase):
    def _items(self):
        """The name of a rule is computed now: identify them by their base"""
        pricelist = self.env["product.pricelist"].search(
            [("name", "=", "OpenUpgrade pricelist")]
        )
        return pricelist.item_ids.sorted("id")

    def test_pricelist_items(self):
        percentage, discount, markup = self._items()
        self.assertEqual(percentage.compute_price, "discount")
        self.assertEqual(percentage.price_discount, 12.5)
        self.assertEqual(discount.compute_price, "discount")
        self.assertEqual(discount.price_discount, 10)
        self.assertEqual(discount.price_surcharge, 2)
        self.assertEqual(markup.compute_price, "markup")
        self.assertEqual(markup.price_markup, 20)

    def test_supplierinfo_uom(self):
        supplierinfo = self.env["product.supplierinfo"].search(
            [("product_tmpl_id.name", "=", "OpenUpgrade product")]
        )
        self.assertEqual(supplierinfo.uom_id, self.env.ref("uom.product_uom_dozen"))

    def test_attribute_exclusions(self):
        value_a = self.env["product.template.attribute.value"].search(
            [
                ("name", "=", "OpenUpgrade A"),
                ("product_tmpl_id.name", "=", "OpenUpgrade variants"),
            ]
        )
        self.assertEqual(value_a.excluded_value_ids.mapped("name"), ["OpenUpgrade X"])

    def test_base_unit(self):
        self.assertTrue(
            self.env["product.base.unit"].search(
                [("name", "=", "OpenUpgrade base unit")]
            )
        )
