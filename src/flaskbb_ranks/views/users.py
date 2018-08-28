import os

from flask import Blueprint

from flaskbb.plugins.models import PluginRegistry
from flaskbb.utils.helpers import render_template

from ..models import Rank

templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
ranks = Blueprint("ranks", __name__, template_folder=templates_dir)


@ranks.route("/")
def index():
    ranks = Rank.partition_ranks(
        Rank.query.order_by(Rank.requirement.asc(), Rank.id).all()
    )

    plugin = PluginRegistry.query.filter_by(name="ranks").first()
    rank_settings = {
        "hide": plugin.settings.get("hide_unapplied_ranks", False),
        "hide_custom": plugin.settings.get("hide_unapplied_custom_ranks", True),
        "name": plugin.settings.get("rank_name_placeholder", "???"),
        "requirement": plugin.settings.get("rank_requirement_placeholder", "???"),
        "code": plugin.settings.get("rank_code_placeholder", "???"),
        "show_users": plugin.settings.get("show_users_for_ranks", True),
        "how_many_users": plugin.settings.get("how_many_users", 5)
    }

    rank_settings["custom_name"] = plugin.settings.get(
        "rank_custom_name_placeholder", rank_settings["name"]
    )
    rank_settings["custom_code"] = plugin.settings.get(
        "rank_custom_code_placeholder", rank_settings["code"]
    )

    return render_template(
        "rank_forum_overview.html",
        ranks=ranks,
        rank_settings=rank_settings,
    )
