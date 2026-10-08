from odoo.tests import TransactionCase

from odoo.addons.openupgrade_framework import openupgrade_test


@openupgrade_test
class TestMailMigration(TransactionCase):
    def _activity_type(self, name):
        return self.env["mail.activity.type"].search([("name", "=", name)])

    def test_activity_type_chaining(self):
        """The triggered type, or the first suggested type by sequence, is
        the new suggested next type"""
        self.assertEqual(
            self._activity_type("OpenUpgrade trigger type").suggested_next_type_id,
            self._activity_type("OpenUpgrade triggered type"),
        )
        self.assertEqual(
            self._activity_type("OpenUpgrade suggest type").suggested_next_type_id,
            self._activity_type("OpenUpgrade suggested type (first)"),
        )

    def test_server_action_log_note(self):
        """A 'Send Message' action with the note method became a 'Log Note'
        action with the body of its template"""
        note = self.env["ir.actions.server"].search(
            [("name", "=", "OpenUpgrade note action")]
        )
        self.assertEqual(note.state, "log_note")
        self.assertIn("OpenUpgrade note body", note.log_note_note)
        comment = self.env["ir.actions.server"].search(
            [("name", "=", "OpenUpgrade comment action")]
        )
        self.assertEqual(comment.state, "mail_post")
        self.assertTrue(comment.template_id)

    def test_bookmarked_message_and_tracking_value(self):
        message = self.env["mail.message"].search(
            [("body", "ilike", "OpenUpgrade starred message")]
        )
        self.assertEqual(len(message), 1)
        self.assertIn(
            self.env.ref("base.partner_admin"), message.bookmarked_partner_ids
        )
