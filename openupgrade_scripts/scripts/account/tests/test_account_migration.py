from odoo.tests import TransactionCase

from odoo.addons.openupgrade_framework import openupgrade_test


@openupgrade_test
class TestAccountMigration(TransactionCase):
    def test_journal_groups(self):
        group = self.env["account.journal.group"].search(
            [("name", "=", "OpenUpgrade ledger group")]
        )
        other = self.env["account.journal.group"].search(
            [("name", "=", "OpenUpgrade other ledger group")]
        )
        company = self.env.ref("base.main_company")
        journals = self.env["account.journal"].search([("company_id", "=", company.id)])
        sale = journals.filtered(lambda journal: journal.type == "sale")[:1]
        self.assertEqual(sale.journal_group_id, other)
        self.assertEqual((journals - sale).journal_group_id, group)

    def test_move_review_state(self):
        reviewed = (
            self.env["account.move.line"]
            .search([("name", "=", "OpenUpgrade reviewed line")])
            .move_id
        )
        self.assertEqual(reviewed.review_state, "reviewed")
        unreviewed = (
            self.env["account.move.line"]
            .search([("name", "=", "OpenUpgrade unreviewed line")])
            .move_id
        )
        self.assertEqual(unreviewed.review_state, "no_review")

    def test_payment_state(self):
        payment = self.env["account.payment"].search(
            [("memo", "=", "OpenUpgrade payment in process")]
        )
        self.assertEqual(payment.state, "paid")
