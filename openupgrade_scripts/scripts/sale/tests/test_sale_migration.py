from odoo.tests import TransactionCase

from odoo.addons.openupgrade_framework import openupgrade_test


@openupgrade_test
class TestSaleMigration(TransactionCase):
    def test_reinvoice_policy(self):
        product = self.env["product.product"].search(
            [("name", "=", "OpenUpgrade reinvoiced service")]
        )
        self.assertEqual(product.reinvoice_policy, "cost")
        self.assertEqual(product.invoice_policy, "delivery")

    def test_customer_lead(self):
        order = self.env["sale.order"].search(
            [("client_order_ref", "=", "OpenUpgrade lead time")]
        )
        self.assertEqual(order.order_line.customer_lead, 3)
