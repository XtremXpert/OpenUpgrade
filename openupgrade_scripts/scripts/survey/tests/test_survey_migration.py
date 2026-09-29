from odoo.tests import TransactionCase

from odoo.addons.openupgrade_framework import openupgrade_test


@openupgrade_test
class TestSurveyMigration(TransactionCase):
    def test_certification_report_layout(self):
        survey = self.env["survey.survey"].search(
            [("title", "=", "OpenUpgrade certification")]
        )
        self.assertEqual(survey.certification_report_layout, "modern_company")
