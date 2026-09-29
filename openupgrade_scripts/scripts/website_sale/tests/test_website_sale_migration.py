from odoo.tests import TransactionCase

from odoo.addons.openupgrade_framework import openupgrade_test


@openupgrade_test
class TestWebsiteSaleMigration(TransactionCase):
    def test_website_options(self):
        website = self.env["website"].search([], limit=1)
        self.assertTrue(website.prevent_sale)
        self.assertEqual(website.prevent_sale_for, "zero_price")
        self.assertTrue(website.send_abandoned_cart_followup)
        self.assertEqual(website.contact_us_link_url, "/openupgrade-contact")
        self.assertTrue(website.show_category_title)

    def test_variant_image(self):
        image = self.env["product.image"].search(
            [("name", "=", "OpenUpgrade red image")]
        )
        self.assertEqual(image.attribute_value_ids.mapped("name"), ["OpenUpgrade red"])
        self.assertTrue(image.has_attribute_value)
