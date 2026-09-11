from flaskbb.extensions import db
from flaskbb.user.models import Guest, User
from flaskbb.utils.database import BaseModel
from sqlalchemy import ForeignKey, select, String
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

__all__ = ("Rank", "UserRank")


class Rank(BaseModel):
    __tablename__ = "ranks"

    id: Mapped[int] = mapped_column(primary_key=True)
    rank_code: Mapped[str] = mapped_column(String(255))
    rank_name: Mapped[str | None] = mapped_column(String(255), default="")
    requirement: Mapped[int | None] = mapped_column(unique=True)

    users = association_proxy("user_ranks", "user", creator=lambda user: UserRank(user=user))

    def is_custom(self):
        return self.requirement is None

    @staticmethod
    def of(user: User | Guest | None) -> "Rank | None":
        if user is None or user.is_anonymous:
            return None
        return user.rank  # type: ignore[union-attr]  # pyright: ignore

    @classmethod
    def has_rank(cls, user: User | Guest | None):
        return cls.of(user) is not None

    @classmethod
    def has_custom_rank(cls, user: User | Guest | None):
        rank = cls.of(user)
        return rank is not None and rank.is_custom()

    @classmethod
    def earned_by(cls, post_count: int):
        return db.session.execute(
            select(cls)
            .where(cls.requirement.is_not(None), cls.requirement <= post_count)
            .order_by(cls.requirement.desc())
            .limit(1)
        ).scalar()

    def __repr__(self):
        return f"<Rank name={self.rank_name} requirement={self.requirement}>"

    @staticmethod
    def partition_ranks(ranks):
        r = {"custom": [], "requirement": []}

        for rank in ranks:
            if rank.is_custom():
                r["custom"].append(rank)
            else:
                r["requirement"].append(rank)

        return r


class UserRank(BaseModel):
    __tablename__ = "user_rank"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    rank_id: Mapped[int | None] = mapped_column(ForeignKey("ranks.id"))

    # selectin instead of joined, a joined eager load corrupts the column
    # layout of Topic.get_posts - https://github.com/flaskbb/flaskbb/issues/503
    user: Mapped[User] = relationship(
        User,
        backref=db.backref(
            "user_rank", uselist=False, lazy="selectin", cascade="all, delete-orphan"
        ),
    )
    rank: Mapped[Rank | None] = relationship(
        Rank,
        lazy="selectin",
        backref=db.backref("user_ranks", cascade="all, delete-orphan"),
    )

    name = association_proxy("rank", "rank_name")
    code = association_proxy("rank", "rank_code")

    def is_custom(self):
        return self.rank is not None and self.rank.is_custom()

    def __repr__(self):
        return f"<UserRank user={self.user.username} name={self.name}>"


User.rank = association_proxy("user_rank", "rank", creator=lambda rank: UserRank(rank=rank))
