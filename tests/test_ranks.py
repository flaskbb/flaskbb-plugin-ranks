from flaskbb.user.models import Guest, User
from flaskbb_ranks.models import Rank, UserRank


class TestRank(object):
    def test_is_custom_returns_false_with_requirement_set(self):
        assert not Rank(requirement=1).is_custom()

    def test_is_custom_returns_true_without_requirement_set(self):
        assert Rank(requirement=None).is_custom()

    def test_has_rank_returns_false_if_user_is_guest(self):
        assert not Rank.has_rank(Guest())

    def test_has_rank_returns_false_if_user_doesnt_have_rank(self):
        assert not Rank.has_rank(User())

    def test_has_rank_returns_true_if_user_has_rank(self):
        assert Rank.has_rank(User(user_rank=UserRank(rank=Rank(requirement=1))))

    def test_has_custom_rank_returns_false_if_user_rank_isnt_custom(self):
        assert not Rank.has_custom_rank(User())

    def test_has_custom_rank_returns_true_if_user_rank_is_custom(self):
        assert Rank.has_custom_rank(
            User(user_rank=UserRank(rank=Rank(requirement=None)))
        )

    def test_partition_ranks_properly_divides_up_ranks(self):
        custom = Rank(requirement=None)
        requirement = Rank(requirement=1)

        paritioned = Rank.partition_ranks([custom, requirement])

        assert paritioned["custom"][0] is custom
        assert paritioned["requirement"][0] is requirement


class TestUserRank(object):
    def test_is_custom_returns_false_if_rank_isnt_custom(self):
        assert not UserRank(rank=Rank(requirement=1)).is_custom()

    def test_is_custom_returns_true_if_rank_is_custom(self):
        assert UserRank(rank=Rank(requirement=None)).is_custom()
