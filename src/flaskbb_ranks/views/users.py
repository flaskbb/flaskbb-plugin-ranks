import os

from flask import Blueprint

from flaskbb.extensions import db
from flaskbb.utils.helpers import render_template

from ..models import Rank

templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
ranks = Blueprint("ranks", __name__, template_folder=templates_dir)


@ranks.route("/")
def index():
    ranks = {"requirement": [], "custom": []}

    for rank in Rank.query.order_by(Rank.requirement.asc(), Rank.id).all():
        if rank.requirement is None:
            ranks["custom"].append(rank)
            continue
        ranks["requirement"].append(rank)

    return render_template("rank_forum_overview.html", ranks=ranks)
