env = locals().get("env")

env["survey.survey"].create(
    {
        "title": "OpenUpgrade certification",
        "certification": True,
        "scoring_type": "scoring_with_answers",
        "certification_report_layout": "modern_gold",
    }
)
env.cr.commit()
