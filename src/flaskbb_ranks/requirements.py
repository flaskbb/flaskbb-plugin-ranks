from flask_allows import Or, Permission, Requirement

from flaskbb.utils.requirements import IsAtleastModerator


class CanViewRankOverview(Requirement):
    def __init__(self, settings):
        self._settings = settings

    def fulfill(self, user):
        return user.is_authenticated or not self._settings.get("hide_from_guests")


class UserCanViewRankDetails(Requirement):
    def __init__(self, rank, settings):
        self._rank = rank
        self._settings = settings

    def fulfill(self, user):
        if len(self._rank.users):
            return True

        if self._rank.is_custom():
            return not self._settings.get("hide_custom")

        return not self._settings.get("hide")


def can_view_rank_details(rank, settings, user):
    return Permission(
        Or(IsAtleastModerator, UserCanViewRankDetails(rank, settings)), identity=user
    )
