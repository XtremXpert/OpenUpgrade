from odoo.tests import TransactionCase

from odoo.addons.openupgrade_framework import openupgrade_test


@openupgrade_test
class TestSmsMigration(TransactionCase):
    def test_server_actions(self):
        note = self.env["ir.actions.server"].search(
            [("name", "=", "OpenUpgrade SMS note action")]
        )
        self.assertEqual(note.state, "log_note")
        self.assertIn("OpenUpgrade SMS body", note.log_note_note)
        sms = self.env["ir.actions.server"].search(
            [("name", "=", "OpenUpgrade SMS sms action")]
        )
        self.assertEqual(sms.state, "sms")
        self.assertTrue(sms.sms_template_id)
