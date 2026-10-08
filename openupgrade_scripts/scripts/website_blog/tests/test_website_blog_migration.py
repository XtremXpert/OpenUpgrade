from odoo.tests import TransactionCase

from odoo.addons.openupgrade_framework import openupgrade_test


@openupgrade_test
class TestWebsiteBlogMigration(TransactionCase):
    def test_publish_on(self):
        post = self.env["blog.post"].search([("name", "=", "OpenUpgrade post")])
        self.assertEqual(str(post.publish_on), "2026-01-02 03:04:05")
