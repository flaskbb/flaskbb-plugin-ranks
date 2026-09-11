import os

from flask import Flask
from flask_allows2 import Permission
from flask_babelplus import gettext as _
from flask_login import current_user
from flaskbb.display.navigation import NavigationLink
from flaskbb.extensions import db
from flaskbb.forum.models import Post
from flaskbb.user.models import Guest, User
from flaskbb.utils.helpers import real, render_template
from flaskbb.utils.requirements import IsAdmin
from pluggy import HookimplMarker

from .models import Rank
from .requirements import CanViewRanks
from .settings import SETTINGS
from .views import ranks, ranks_management

ranks_impl = HookimplMarker("flaskbb")


@ranks_impl
def flaskbb_load_migrations():
    return os.path.join(os.path.dirname(__file__), "migrations")


@ranks_impl
def flaskbb_load_setting_groups():
    return SETTINGS


@ranks_impl
def flaskbb_load_blueprints(app: Flask):
    app.register_blueprint(ranks, url_prefix="/ranks")
    app.register_blueprint(ranks_management, url_prefix="/management/ranks")


@ranks_impl
def flaskbb_tpl_navigation_after():
    if Permission(CanViewRanks(), identity=real(current_user)):
        return NavigationLink(endpoint="ranks.index", name=_("Ranks"), icon="fa fa-id-badge")


@ranks_impl
def flaskbb_tpl_post_author_info_before(user: User | None, post: Post):
    rank = Rank.of(user)
    if rank is not None:
        return render_template("rank_rank_in_post.html", rank=rank)


@ranks_impl
def flaskbb_tpl_profile_stats(user: User):
    rank = Rank.of(user)
    if rank is not None:
        return render_template("rank_profile_stats.html", rank=rank)


@ranks_impl
def flaskbb_tpl_admin_settings_menu(user: User | Guest):
    if Permission(IsAdmin, identity=user):
        return [("ranks_management.index", "Ranks", "fa fa-id-badge")]
    return []


@ranks_impl
def flaskbb_event_post_save_after(post: Post, is_new: bool):
    user = post.user
    if not is_new or user is None or Rank.has_custom_rank(user):
        return

    earned = Rank.earned_by(user.post_count)
    if earned is None or earned is Rank.of(user):
        return

    user.rank = earned  # type: ignore[attr-defined]  # pyright: ignore
    db.session.commit()
