import os

from pluggy import HookimplMarker

from flaskbb.extensions import db
from flaskbb.utils.helpers import render_template

from . import models, views
from .models import Rank

__all__ = ("ranks_impl", "models")

ranks_impl = HookimplMarker("flaskbb")


def render_rank(user):
    if Rank.has_rank(user):
        return render_template("rank_rank_in_post.html", rank=user.rank)


@ranks_impl
def flaskbb_load_migrations():
    return os.path.join(os.path.dirname(__file__), "migrations")


@ranks_impl
def flaskbb_tpl_post_author_info_before(user, post):
    return render_rank(user)


@ranks_impl
def flaskbb_tpl_profile_sidebar_stats(user):
    return render_rank(user)


@ranks_impl
def flaskbb_load_blueprints(app):
    app.register_blueprint(views.ranks, url_prefix="/ranks")
    app.register_blueprint(views.ranks_management, url_prefix="/management/ranks")


@ranks_impl
def flaskbb_additional_setup():
    models._monkeypatch_user()


@ranks_impl
def flaskbb_tpl_navigation_after():
    return render_template("rank_top_bar_navigation.html")


@ranks_impl
def flaskbb_event_post_save_after(post, is_new):
    if not is_new:
        return

    user = post.user

    # either guest or custom rank, don't do anything.
    # careful, user might not have one yet
    if user.is_anonymous or Rank.has_custom_rank(user):
        return

    if not Rank.has_rank(user):
        rank = (
            Rank.query.filter(
                Rank.requirement <= user.post_count, Rank.requirement != None
            )
            .order_by(Rank.requirement.desc())
            .first()
        )
        user.rank = rank

    else:

        next_rank = (
            Rank.query.filter(
                Rank.requirement > user.rank.requirement,
                Rank.requirement != None,
                Rank.requirement <= user.post_count,
            )
            .order_by(Rank.requirement.asc())
            .first()
        )

        if next_rank is not None:
            user.rank = next_rank

    db.session.commit()


@ranks_impl
def flaskbb_tpl_admin_settings_menu(user):
    return [("ranks_management.index", "Ranks", "fa fa-id-badge")]
