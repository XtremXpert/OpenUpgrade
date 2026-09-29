env = locals().get("env")

forum = env["forum.forum"].search([], limit=1) or env["forum.forum"].create(
    {"name": "OpenUpgrade forum"}
)
post = env["forum.post"].create(
    {"name": "OpenUpgrade question", "forum_id": forum.id, "content": "<p>Why?</p>"}
)
post.message_post(body="<p>OpenUpgrade comment</p>", message_type="comment")
post.message_subscribe(partner_ids=env.ref("base.main_partner").ids)
env.cr.commit()
