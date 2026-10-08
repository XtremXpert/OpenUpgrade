from odoo.tests import TransactionCase

from odoo.addons.openupgrade_framework import openupgrade_test


@openupgrade_test
class TestWebsiteForumMigration(TransactionCase):
    def test_post_comments_and_followers(self):
        post = self.env["forum.post"].search([("name", "=", "OpenUpgrade question")])
        self.assertEqual(len(post), 1)
        self.assertIn("OpenUpgrade comment", post.comment_ids.body)
        self.assertIn(self.env.ref("base.main_partner"), post.sudo().follower_ids)
        self.assertTrue(post.write_date_content)
