import os

from pluggy import HookimplMarker

from flaskbb.extensions import db
from flaskbb.utils.forms import SettingValueType
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


SETTINGS = {
    "hide_unapplied_ranks": {
        "value": False,
        "value_type": SettingValueType.boolean,
        "name": "Hide Unapplied Ranks",
        "description": "Hides ranks with no users attached in the forum overview. Replaces displays with placeholders.",
        "extra": {},
    },
    "rank_name_placeholder": {
        "value": "???",
        "value_type": SettingValueType.string,
        "name": "Rank Name Placehold",
        "description": "Placeholder when a rank name is hidden in the forum overview.",
        "extra": {},
    },
    "rank_code_placeholder": {
        "value": "???",
        "value_type": SettingValueType.string,
        "name": "Rank Display Placeholder",
        "description": "Placeholder when a rank display is hidden in the forum overview. May be markdown.",
        "extra": {},
    },
    "rank_requirement_placeholder": {
        "value": "???",
        "value_type": SettingValueType.string,
        "name": "Rank Requirement Placehold",
        "description": "Placeholder when a rank requirement is hidden in the forum overview. Set to blank to show requirement.",
        "extra": {},
    },
    "hide_unapplied_custom_ranks": {
        "value": True,
        "value_type": SettingValueType.boolean,
        "name": "Hide Unapplied Custom Ranks",
        "description": "Hides custom ranks with no users attached in the forum overview. Replaces displays with placeholders.",
        "extra": {},
    },
    "rank_custom_name_placeholder": {
        "value": "???",
        "value_type": SettingValueType.string,
        "name": "Rank Name Placehold",
        "description": "Placeholder when a custom rank name is hidden in the forum overview. If not set, will use the regular name placeholder.",
        "extra": {},
    },
    "rank_custom_code_placeholder": {
        "value": "???",
        "value_type": SettingValueType.string,
        "name": "Custom Rank Display Placeholder",
        "description": "Placeholder when a custom rank display is hidden in the forum overview. May be markdown. If not set, will use the regular display placeholder.",
        "extra": {},
    },
    "show_users_for_ranks": {
        "value": True,
        "value_type": SettingValueType.boolean,
        "name": "Show users with rank in forum overview",
        "description": "",
        "extra": {},
    },
    "how_many_users": {
        "value": 5,
        "value_type": SettingValueType.integer,
        "name": "How many users to show",
        "description": "If showing users on the forum overview, how many users to show.",
        "extra": {},
    },
    "hide_from_guests": {
        "value": True,
        "value_type": SettingValueType.boolean,
        "name": "Hide rank overview from guests",
        "description": "Hides rank list and rank details from guests",
        "extra": {},
    },
}
