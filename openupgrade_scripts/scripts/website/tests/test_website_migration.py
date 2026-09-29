from odoo.tests import TransactionCase

from odoo.addons.openupgrade_framework import openupgrade_test


@openupgrade_test
class TestWebsiteMigration(TransactionCase):
    def test_page(self):
        page = self.env["website.page"].search([("url", "=", "/openupgrade-test-page")])
        self.assertEqual(len(page), 1)
        self.assertEqual(page.name, "OpenUpgrade test page")
        self.assertEqual(str(page.publish_on), "2026-01-02 03:04:05")
        self.assertEqual(page.visibility, "public")

    def test_menus(self):
        external = self.env["website.menu"].search(
            [("name", "=", "OpenUpgrade external menu")]
        )
        self.assertEqual(external.manual_url, "https://example.com/openupgrade")
        self.assertEqual(external.url, "https://example.com/openupgrade")
        page_menu = self.env["website.menu"].search(
            [("name", "=", "OpenUpgrade page menu")]
        )
        self.assertFalse(page_menu.manual_url)
        self.assertEqual(page_menu.url, "/openupgrade-test-page")

    def test_social_links_moved_to_company(self):
        website = self.env["website"].search([], limit=1)
        self.assertEqual(
            website.company_id.social_facebook, "https://facebook.com/openupgrade"
        )
