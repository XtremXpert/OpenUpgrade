from odoo.tests import TransactionCase

from odoo.addons.openupgrade_framework import openupgrade_test


@openupgrade_test
class TestPaymentMigration(TransactionCase):
    def _provider(self, name):
        return (
            self.env["payment.provider"]
            .with_context(active_test=False)
            .search([("name", "=", name)])
        )

    def _methods(self, code):
        return (
            self.env["payment.method"]
            .with_context(active_test=False)
            .search([("code", "=", code)])
        )

    def test_provider_state(self):
        live = self._provider("OpenUpgrade live provider")
        self.assertTrue(live.active)
        self.assertTrue(live.is_live)
        test = self._provider("OpenUpgrade test provider")
        self.assertTrue(test.active)
        self.assertFalse(test.is_live)
        disabled = self._provider("OpenUpgrade disabled provider")
        self.assertFalse(disabled.active)
        self.assertFalse(disabled.is_live)

    def test_shared_method_split(self):
        live = self._provider("OpenUpgrade live provider")
        test = self._provider("OpenUpgrade test provider")
        methods = self._methods("openupgrade_shared")
        self.assertEqual(len(methods), 2)
        self.assertEqual(methods.provider_id, live + test)
        brands = self._methods("openupgrade_brand")
        self.assertEqual(len(brands), 2)
        for brand in brands:
            self.assertEqual(
                brand.primary_payment_method_id.provider_id, brand.provider_id
            )

    def test_method_of_token(self):
        method = self._methods("openupgrade_token")
        self.assertEqual(
            method.provider_id, self._provider("OpenUpgrade test provider")
        )
        token = self.env["payment.token"].search(
            [("payment_details", "=", "OpenUpgrade token")]
        )
        self.assertEqual(token.payment_method_id, method)

    def test_unused_method_removed(self):
        self.assertFalse(self._methods("openupgrade_unused"))
