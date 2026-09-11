from flask_allows2 import Or, Permission, Requirement
from flaskbb.user.models import Guest, User
from flaskbb.utils.requirements import IsAtleastModerator

from .models import Rank
from .settings import rank_setting


class CanViewRanks(Requirement):
    def fulfill(self, user: User | Guest):
        return user.is_authenticated or not rank_setting("HIDE_FROM_GUESTS")


class RankIsVisible(Requirement):
    def __init__(self, rank: Rank):
        self.rank = rank

    def fulfill(self, user: User | Guest):
        if self.rank.users:
            return True
        if self.rank.is_custom():
            return not rank_setting("HIDE_UNAPPLIED_CUSTOM_RANKS")
        return not rank_setting("HIDE_UNAPPLIED_RANKS")


def can_view_rank_details(rank: Rank, user: User | Guest):
    return Permission(Or(IsAtleastModerator, RankIsVisible(rank)), identity=user)
