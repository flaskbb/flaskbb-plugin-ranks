from sqlalchemy.ext.associationproxy import association_proxy

from flaskbb.extensions import db
from flaskbb.user.models import User

__all__ = ("Rank", "UserRank")


class Rank(db.Model):
    __tablename__ = "ranks"
    id = db.Column(db.Integer(), primary_key=True)
    rank_code = db.Column(db.String(255), nullable=False)
    rank_name = db.Column(db.String(255), default="")
    requirement = db.Column(db.Integer(), nullable=True, unique=True)

    users = association_proxy(
        "user_ranks", "user", creator=lambda user: UserRank(user=user)
    )

    def __repr__(self):
        return "<Rank name={} requirement={}>".format(self.rank_name, self.requirement)


class UserRank(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.ForeignKey("users.id"), nullable=False)
    rank_id = db.Column(db.ForeignKey("ranks.id"))
    user = db.relationship(
        User,
        backref=db.backref(
            "user_rank", uselist=False, cascade="all, delete-orphan", lazy="joined"
        ),
        uselist=False,
        lazy="joined",
        foreign_keys=[user_id],
    )

    rank = db.relationship(
        Rank,
        backref=db.backref("user_ranks", lazy="joined", cascade="all, delete-orphan"),
        uselist=False,
        lazy="joined",
        foreign_keys=[rank_id],
    )

    name = association_proxy("rank", "rank_name")
    code = association_proxy("rank", "rank_code")

    def __repr__(self):
        return "<UserRank user={} name={}>".format(self.user.username, self.name)


def _monkeypatch_user():
    User.rank = association_proxy(
        "user_rank", "rank", creator=lambda r: UserRank(rank=r)
    )
