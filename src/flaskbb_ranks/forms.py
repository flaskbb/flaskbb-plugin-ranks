from flask_babelplus import gettext as _
from wtforms import HiddenField, IntegerField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional

from flaskbb.utils.forms import FlaskBBForm


class BaseRankForm(FlaskBBForm):
    rank_name = StringField(
        "Rank Name", validators=[DataRequired("Must enter rank name")]
    )
    rank_code = TextAreaField(
        "Rank Code", validators=[DataRequired("Must enter rank code")]
    )
    requirement = IntegerField(
        "Post Requirement", validators=[Optional(strip_whitespace=True)]
    )


class AddRankForm(BaseRankForm):
    submit = SubmitField("Add Rank")


class EditRankForm(BaseRankForm):
    id = HiddenField()
    submit = SubmitField("Edit Rank")


class DeleteRankForm(FlaskBBForm):
    id = HiddenField()
    submit = SubmitField("Delete Rank")


class ApplyCustomRankForm(FlaskBBForm):
    id = HiddenField()
    username = StringField(
        _("Username"), validators=[DataRequired("Must enter username")]
    )
    submit = SubmitField("Apply rank")
