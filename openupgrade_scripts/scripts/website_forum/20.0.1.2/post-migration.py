# Copyright 2026 Benoit Vézina
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


def _post_comments(cr):
    """Posts and tags are not mail threads anymore: the comments posted on
    a post become forum.post.comment records, and the followers become
    partners in follower_ids."""
    openupgrade.logged_query(
        cr,
        """
        INSERT INTO forum_post_comment
            (post_id, body, create_uid, create_date, write_uid, write_date)
        SELECT message.res_id, message.body,
               COALESCE(message.create_uid, 1), message.create_date,
               COALESCE(message.write_uid, 1), message.write_date
        FROM mail_message message
        JOIN forum_post post ON post.id = message.res_id
        WHERE message.model = 'forum.post' AND message.message_type = 'comment'
            AND message.body IS NOT NULL AND message.body != ''
        ORDER BY message.id
        """,
    )
    for model, table in (("forum.post", "forum_post"), ("forum.tag", "forum_tag")):
        openupgrade.logged_query(
            cr,
            f"""
            INSERT INTO {table}_follower_rel ({table}_id, res_partner_id)
            SELECT follower.res_id, follower.partner_id
            FROM mail_followers follower
            JOIN {table} record ON record.id = follower.res_id
            WHERE follower.res_model = %s AND follower.partner_id IS NOT NULL
            ON CONFLICT DO NOTHING
            """,
            (model,),
        )
    openupgrade.logged_query(
        cr,
        "UPDATE forum_post SET write_date_content = write_date "
        "WHERE write_date_content IS NULL",
    )


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.load_data(env, "website_forum", "20.0.1.2/noupdate_changes.xml")
    _post_comments(env.cr)
