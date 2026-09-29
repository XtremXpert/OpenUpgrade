env = locals().get("env")

blog = env["blog.blog"].search([], limit=1) or env["blog.blog"].create(
    {"name": "OpenUpgrade blog"}
)
env["blog.post"].create(
    {
        "name": "OpenUpgrade post",
        "blog_id": blog.id,
        "post_date": "2026-01-02 03:04:05",
        "content": "<p>OpenUpgrade</p>",
    }
)
env.cr.commit()
