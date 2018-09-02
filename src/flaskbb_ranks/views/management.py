import os

from flask import Blueprint, flash, redirect, url_for
from flask.views import MethodView

from flaskbb.extensions import db
from flaskbb.user.models import User
from flaskbb.utils.helpers import register_view, render_template

from ..forms import (
    AddRankForm,
    ApplyCustomRankForm,
    DeleteRankForm,
    EditRankForm,
    ResyncForm,
)
from ..models import Rank

templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")


ranks_management = Blueprint(
    "ranks_management", __name__, template_folder=templates_dir
)


@ranks_management.route("/")
def index():
    ranks = Rank.query.order_by(Rank.requirement.asc())
    return render_template("ranks_management_overview.html", ranks=ranks)


class AddRankView(MethodView):
    def get(self):
        return render_template("rank_management_add.html", form=AddRankForm())

    def post(self):
        form = AddRankForm()
        if form.validate_on_submit():
            rank = Rank(
                rank_name=form.rank_name.data,
                rank_code=form.rank_code.data,
                requirement=form.requirement.data,
            )
            db.session.add(rank)
            db.session.commit()
            flash("{} added!".format(rank.rank_name), "success")
            return redirect(url_for("ranks_management.index"))
        return render_template("rank_management_add.html", form=form)


class EditRankView(MethodView):
    def get(self, id):
        rank = Rank.query.get_or_404(id)
        return render_template(
            "rank_management_edit.html", form=EditRankForm(obj=rank), rank=rank
        )

    def post(self, id):
        rank = Rank.query.get_or_404(id)
        form = EditRankForm(obj=rank)
        if form.validate_on_submit():
            form.populate_obj(rank)
            db.session.commit()
            flash("{} updated!".format(rank.rank_name), "success")
            return redirect(url_for("ranks_management.index"))
        return render_template("rank_management_edit.html", form=form, rank=rank)


class DeleteRankView(MethodView):
    def get(self, id):
        rank = Rank.query.get_or_404(id)
        return render_template(
            "rank_management_delete.html", form=DeleteRankForm(), rank=rank
        )

    def post(self, id):
        rank = Rank.query.get_or_404(id)
        form = DeleteRankForm()

        if form.validate_on_submit():
            db.session.delete(rank)
            db.session.commit()
            flash("{} deleted".format(rank.rank_name), "success")
            return redirect(url_for("ranks_management.index"))

        return render_template("ranks_management_delete.html", form=form, rank=rank)


class ApplyCustomRank(MethodView):
    def get(self, id):
        rank = Rank.query.get_or_404(id)
        form = ApplyCustomRankForm()
        return render_template("rank_management_apply.html", form=form, rank=rank)

    def post(self, id):
        rank = Rank.query.get_or_404(id)
        form = ApplyCustomRankForm()

        if form.validate_on_submit():
            user = User.query.filter(User.username == form.username.data).first_or_404()
            user.rank = rank
            db.session.commit()
            flash(
                "Rank {} given to {}".format(rank.rank_name, user.username), "success"
            )
            return redirect(url_for("ranks_management.index"))

        return render_template("ranks_management_apply.html", form=form, rank=rank)


register_view(
    ranks_management,
    routes=["/delete/<id>"],
    view_func=DeleteRankView.as_view("delete_rank"),
)
register_view(
    ranks_management, routes=["/edit/<id>"], view_func=EditRankView.as_view("edit_rank")
)
register_view(
    ranks_management, routes=["/add"], view_func=AddRankView.as_view("add_rank")
)
register_view(
    ranks_management,
    routes=["/apply/<id>"],
    view_func=ApplyCustomRank.as_view("apply_rank"),
)
