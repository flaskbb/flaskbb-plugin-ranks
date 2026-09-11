import os

from flask import abort, Blueprint
from flask_babelplus import lazy_gettext
from flask_login import current_user
from flaskbb.extensions import allows, db
from flaskbb.utils.helpers import FlashAndRedirect, real, render_template
from sqlalchemy import select

from ..models import Rank
from ..requirements import can_view_rank_details, CanViewRanks
from ..settings import rank_setting

templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
ranks = Blueprint("ranks", __name__, template_folder=templates_dir)


@ranks.before_request
@allows.requires(
    CanViewRanks(),
    on_fail=FlashAndRedirect(
        message=lazy_gettext("You need to be logged in to view the ranks"),
        level="warning",
        endpoint="auth.login",
    ),
)
def check_can_view_ranks():
    pass


@ranks.context_processor
def inject_rank_setting():
    return {"rank_setting": rank_setting}


@ranks.route("/")
def index():
    all_ranks = db.session.execute(select(Rank).order_by(Rank.requirement.asc(), Rank.id)).scalars()

    return render_template("rank_forum_overview.html", ranks=Rank.partition_ranks(all_ranks))


@ranks.route("/<int:rank_id>")
def rank_detail(rank_id: int):
    rank = Rank.get_or_404(Rank.id == rank_id)
    if not can_view_rank_details(rank, real(current_user)):
        abort(404)
    return render_template("rank_forum_detail.html", rank=rank)
