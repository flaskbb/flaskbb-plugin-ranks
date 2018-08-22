import pytest
from flaskbb_ranks.models import _monkeypatch_user


@pytest.fixture(scope="session", autouse=True)
def patch_user():
    _monkeypatch_user()
