from odoo.tests import TransactionCase

from odoo.addons.openupgrade_framework import openupgrade_test


@openupgrade_test
class TestMassMailingMigration(TransactionCase):
    def test_mailing_filters(self):
        mailing = self.env["mailing.mailing"].search(
            [("subject", "=", "OpenUpgrade mailing")]
        )
        self.assertEqual(
            mailing.mailing_filter_ids.mapped("name"), ["OpenUpgrade filter"]
        )
