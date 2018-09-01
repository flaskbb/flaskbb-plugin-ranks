import os

from flask import Blueprint

from flaskbb.plugins.models import PluginRegistry
from flaskbb.utils.helpers import render_template

from ..models import Rank
from ..locals import rank_settings

templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
ranks = Blueprint("ranks", __name__, template_folder=templates_dir)


@ranks.route("/")
def index():
    ranks = Rank.partition_ranks(
        Rank.query.order_by(Rank.requirement.asc(), Rank.id).all()
    )

    return render_template(
        "rank_forum_overview.html",
        ranks=ranks,
        rank_settings=rank_settings,
    )


@ranks.route("/<int:rank_id>")
def rank_detail(rank_id):
    rank = Rank.query.get_or_404(rank_id)
    return render_template("rank_forum_detail.html", rank=rank, rank_settings=rank_settings)
