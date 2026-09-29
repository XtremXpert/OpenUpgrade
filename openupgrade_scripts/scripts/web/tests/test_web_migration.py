from odoo.tests import TransactionCase

from odoo.addons.openupgrade_framework import openupgrade_test


@openupgrade_test
class TestWebMigration(TransactionCase):
    def test_company_report_layout(self):
        """The Bold layout became the bold table design on the Light layout"""
        company = self.env["res.company"].search(
            [("name", "=", "OpenUpgrade bold company")]
        )
        self.assertEqual(
            company.external_report_layout_id,
            self.env.ref("web.external_layout_standard"),
        )
        self.assertEqual(company.report_tables_id, "bold")
