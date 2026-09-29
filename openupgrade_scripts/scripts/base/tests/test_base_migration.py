from odoo.tests import TransactionCase

from odoo.addons.openupgrade_framework import openupgrade_test


@openupgrade_test
class TestBaseMigration(TransactionCase):
    def _accesses(self, model, **domain):
        return (
            self.env["ir.access"]
            .with_context(active_test=False)
            .search(
                [("model_id.model", "=", model)]
                + [(key, "=", value) for key, value in domain.items()]
            )
        )

    def test_custom_access_converted(self):
        """A custom ACL becomes a permission of its group, with the domain of
        the group rule folded in for the operations the rule applies to"""
        group = self.env["res.groups"].search([("name", "=", "OpenUpgrade test group")])
        self.assertTrue(group)
        accesses = self._accesses("res.partner.category", group_id=group.id)
        self.assertEqual(len(accesses), 2)
        read = accesses.filtered(lambda access: access.operation == "r")
        write = accesses.filtered(lambda access: access.operation == "u")
        self.assertTrue(read.active)
        self.assertIn("openupgrade", read.domain)
        self.assertTrue(write.active)
        self.assertFalse(write.domain)

    def test_custom_global_rule_converted(self):
        """A custom global rule becomes a restriction"""
        restriction = self._accesses(
            "res.partner.category", name="OpenUpgrade test global rule"
        )
        self.assertEqual(len(restriction), 1)
        self.assertFalse(restriction.group_id)
        self.assertEqual(restriction.operation, "crud")
        self.assertIn("secret", restriction.domain)

    def test_custom_group_rule_restricts_standard_permission(self):
        """A custom group rule replaces the standard permission of its group
        by a restricted copy"""
        standard = self.env.ref("base.access_res_partner_industry_group_user")
        self.assertFalse(standard.active)
        copies = self._accesses(
            "res.partner.industry", group_id=standard.group_id.id, active=True
        ).filtered(lambda access: access.operation == "r")
        self.assertTrue(copies)
        self.assertTrue(all("hidden" in access.domain for access in copies))

    def test_deactivated_standard_access_stays_deactivated(self):
        self.assertFalse(
            self.env.ref("base.access_res_partner_industry_group_system").active
        )

    def test_partner_bank(self):
        bank = self.env["res.partner.bank"].search(
            [("account_number", "=", "OPENUPGRADE-TEST-123")]
        )
        self.assertEqual(bank.bank_name, "OpenUpgrade test bank")
        self.assertEqual(bank.bank_bic, "OPUPCAM1")
        self.assertEqual(bank.city, "Montréal")
        self.assertEqual(bank.country_id, self.env.ref("base.ca"))
        self.assertTrue(bank.clearing_label_id)
        self.assertTrue(bank.holder_name)

    def test_client_action_params(self):
        action = self.env["ir.actions.client"].search(
            [("name", "=", "OpenUpgrade test client action")]
        )
        self.assertEqual(action.params, {"openupgrade": 1})

    def test_country_zip_applicability(self):
        country = self.env["res.country"].search([("code", "=", "XT")])
        self.assertEqual(country.zip_applicability, "optional")
        self.assertEqual(self.env.ref("base.ca").zip_applicability, "required")

    def test_model_fields_index(self):
        field = self.env["ir.model.fields"].search(
            [("name", "=", "x_openupgrade_test")]
        )
        self.assertEqual(field.index, "btree")
