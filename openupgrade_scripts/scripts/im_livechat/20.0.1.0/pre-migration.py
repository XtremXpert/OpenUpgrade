# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


def _livechat_status(cr):
    """The 'waiting for customer' status is gone"""
    openupgrade.logged_query(
        cr,
        """
        UPDATE discuss_channel SET livechat_status = 'in_progress'
        WHERE livechat_status = 'waiting'
        """,
    )


def _livechat_rating(env):
    """The last rating value (1, 3 or 5) became the livechat_rating selection"""
    openupgrade.add_fields(
        env,
        [
            (
                "livechat_rating",
                "discuss.channel",
                "discuss_channel",
                "selection",
                False,
                "im_livechat",
            )
        ],
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE discuss_channel
        SET livechat_rating = CASE
            WHEN rating_last_value >= 5 THEN '5'
            WHEN rating_last_value >= 3 THEN '3'
            WHEN rating_last_value > 0 THEN '1'
        END
        WHERE channel_type = 'livechat' AND rating_last_value > 0
        """,
    )


@openupgrade.migrate()
def migrate(env, version):
    _livechat_status(env.cr)
    _livechat_rating(env)
