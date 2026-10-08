env = locals().get("env")

company = env.ref("base.main_company")
journals = env["account.journal"].search([("company_id", "=", company.id)], order="id")
sale_journal = journals.filtered(lambda journal: journal.type == "sale")[:1]
other_journals = journals - sale_journal

# ledger groups excluding some journals
env["account.journal.group"].create(
    {
        "name": "OpenUpgrade ledger group",
        "company_id": company.id,
        "sequence": 1,
        "excluded_journal_ids": [(6, 0, sale_journal.ids)],
    }
)
env["account.journal.group"].create(
    {
        "name": "OpenUpgrade other ledger group",
        "company_id": company.id,
        "sequence": 2,
        "excluded_journal_ids": [(6, 0, other_journals.ids)],
    }
)

# a reviewed and a non reviewed entry
Move = env["account.move"]
partner = env.ref("base.main_partner")
reviewed = Move.create(
    {
        "move_type": "out_invoice",
        "partner_id": partner.id,
        "invoice_line_ids": [
            (
                0,
                0,
                {"name": "OpenUpgrade reviewed line", "quantity": 1, "price_unit": 10},
            )
        ],
    }
)
reviewed.action_post()
reviewed.checked = True
Move.create(
    {
        "move_type": "out_invoice",
        "partner_id": partner.id,
        "invoice_line_ids": [
            (
                0,
                0,
                {
                    "name": "OpenUpgrade unreviewed line",
                    "quantity": 1,
                    "price_unit": 20,
                },
            )
        ],
    }
)

# a payment in process
bank_journal = journals.filtered(lambda journal: journal.type == "bank")[:1]
payment = env["account.payment"].create(
    {
        "payment_type": "inbound",
        "partner_type": "customer",
        "partner_id": partner.id,
        "amount": 5,
        "journal_id": bank_journal.id,
        "memo": "OpenUpgrade payment in process",
    }
)
payment.action_post()
env.cr.commit()
