from odoo.tests import TransactionCase

from odoo.addons.openupgrade_framework import openupgrade_test


@openupgrade_test
class TestMailTrackingMigration(TransactionCase):
    def test_tracking_values_kept(self):
        """mail.tracking.value moved here from mail, with its data"""
        message = self.env["mail.message"].search(
            [("body", "ilike", "OpenUpgrade starred message")]
        )
        self.assertEqual(message.message_type, "tracking")
        tracking = self.env["mail.tracking.value"].search(
            [("mail_message_id", "=", message.id)]
        )
        self.assertEqual(tracking.new_value_char, "OpenUpgrade new name")
