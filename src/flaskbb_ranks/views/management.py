import os

from flask import Blueprint, flash, redirect, url_for
from flask.views import MethodView
from flask_babelplus import gettext as _
from flask_babelplus import lazy_gettext
from flask_login import login_fresh
from flaskbb.extensions import allows, db, login_manager
from flaskbb.user.models import User
from flaskbb.utils.helpers import FlashAndRedirect, register_view, render_template
from flaskbb.utils.requirements import IsAdmin
from sqlalchemy import select

from ..forms import ApplyCustomRankForm, DeleteRankForm, RankForm
from ..models import Rank

templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")


ranks_management = Blueprint("ranks_management", __name__, template_folder=templates_dir)


@ranks_management.before_request
@allows.requires(
    IsAdmin,
    on_fail=FlashAndRedirect(
        message=lazy_gettext("You are not allowed to manage ranks"),
        level="danger",
        endpoint="forum.index",
    ),
)
def check_fresh_admin():
    if not login_fresh():
        return login_manager.needs_refresh()


@ranks_management.route("/")
def index():
    ranks = db.session.execute(select(Rank).order_by(Rank.requirement.asc(), Rank.id)).scalars()
    return render_template("ranks_management_overview.html", ranks=ranks)


class AddRankView(MethodView):
    def get(self):
        return render_template("rank_management_form.html", form=RankForm(), title=_("Add Rank"))

    def post(self):
        form = RankForm()
        if form.validate_on_submit():
            rank = Rank.create(
                rank_name=form.rank_name.data,
                rank_code=form.rank_code.data,
                requirement=form.requirement.data,
            )
            flash(_("%(name)s added!", name=rank.rank_name), "success")
            return redirect(url_for("ranks_management.index"))
        return render_template("rank_management_form.html", form=form, title=_("Add Rank"))


class EditRankView(MethodView):
    def get(self, rank_id: int):
        rank = Rank.get_or_404(Rank.id == rank_id)
        return render_template(
            "rank_management_form.html", form=RankForm(obj=rank), title=_("Edit Rank")
        )

    def post(self, rank_id: int):
        rank = Rank.get_or_404(Rank.id == rank_id)
        form = RankForm(obj=rank)
        if form.validate_on_submit():
            form.populate_obj(rank, exclude=("submit",))
            rank.save()
            flash(_("%(name)s updated!", name=rank.rank_name), "success")
            return redirect(url_for("ranks_management.index"))
        return render_template("rank_management_form.html", form=form, title=_("Edit Rank"))


class DeleteRankView(MethodView):
    def post(self, rank_id: int):
        rank = Rank.get_or_404(Rank.id == rank_id)
        if DeleteRankForm().validate_on_submit():
            name = rank.rank_name
            rank.delete()
            flash(_("%(name)s deleted", name=name), "success")
        return redirect(url_for("ranks_management.index"))


class ApplyCustomRankView(MethodView):
    def get(self, rank_id: int):
        rank = Rank.get_or_404(Rank.id == rank_id, Rank.requirement.is_(None))
        return render_template("rank_management_apply.html", form=ApplyCustomRankForm(), rank=rank)

    def post(self, rank_id: int):
        rank = Rank.get_or_404(Rank.id == rank_id, Rank.requirement.is_(None))
        form = ApplyCustomRankForm()

        if form.validate_on_submit():
            user = User.get_by(username=form.username.data)
            if user is not None:
                user.rank = rank  # pyright: ignore
                db.session.commit()
                flash(
                    _(
                        "Rank %(rank)s given to %(user)s",
                        rank=rank.rank_name,
                        user=user.username,
                    ),
                    "success",
                )
                return redirect(url_for("ranks_management.index"))
            form.populate_errors([("username", _("No user with that username exists."))])

        return render_template("rank_management_apply.html", form=form, rank=rank)


register_view(
    ranks_management,
    routes=["/delete/<int:rank_id>"],
    view_func=DeleteRankView.as_view("delete_rank"),
)
register_view(
    ranks_management,
    routes=["/edit/<int:rank_id>"],
    view_func=EditRankView.as_view("edit_rank"),
)
register_view(ranks_management, routes=["/add"], view_func=AddRankView.as_view("add_rank"))
register_view(
    ranks_management,
    routes=["/apply/<int:rank_id>"],
    view_func=ApplyCustomRankView.as_view("apply_rank"),
)
