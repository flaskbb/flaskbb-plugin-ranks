import os
from pluggy import HookimplMarker

ranks_impl = HookimplMarker("flaskbb")

@ranks_impl
def flaskbb_load_migrations():
    return os.path.join(os.path.dirname(__file__), "migrations")

@ranks_impl
def flaskbb_tpl_post_author_info_before(user, post):
    return "I'd be a rank!!!"
