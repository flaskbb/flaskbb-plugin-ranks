from flask_babelplus import lazy_gettext as _
from flaskbb.utils.forms import FlaskBBForm
from wtforms import IntegerField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional


class RankForm(FlaskBBForm):
    rank_name = StringField(_("Rank Name"), validators=[DataRequired(_("Must enter rank name"))])
    rank_code = TextAreaField(_("Rank Code"), validators=[DataRequired(_("Must enter rank code"))])
    requirement = IntegerField(
        _("Post Requirement"),
        description=_("Leave empty for a custom rank that is handed out manually."),
        validators=[Optional(strip_whitespace=True)],
    )
    submit = SubmitField(_("Save"))


class DeleteRankForm(FlaskBBForm):
    pass


class ApplyCustomRankForm(FlaskBBForm):
    username = StringField(_("Username"), validators=[DataRequired(_("Must enter username"))])
    submit = SubmitField(_("Apply rank"))
