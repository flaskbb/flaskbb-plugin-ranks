import os

from flask import Blueprint

from flaskbb.utils.helpers import render_template

from ..models import Rank

templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
ranks = Blueprint("ranks", __name__, template_folder=templates_dir)


@ranks.route("/")
def index():
    ranks = Rank.partition_ranks(
        Rank.query.order_by(Rank.requirement.asc(), Rank.id).all()
    )

    return render_template("rank_forum_overview.html", ranks=ranks)
