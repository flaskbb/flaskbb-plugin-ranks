import pytest
from flask import g
from flask_login.test_client import FlaskLoginClient
from flaskbb.extensions import db
from flaskbb.forum.models import Post
from flaskbb.settings import Setting

from flaskbb_ranks import flaskbb_event_post_save_after
from flaskbb_ranks.models import Rank
from flaskbb_ranks.settings import SETTINGS


@pytest.fixture
def client(application, default_settings, default_groups, monkeypatch):
    # FlaskLoginClient doesn't store the session identifier, so "basic"
    # session protection would mark every login as stale on the first request
    monkeypatch.setattr(application.login_manager, "session_protection", None)
    monkeypatch.setattr(application, "test_client_class", FlaskLoginClient)

    def make(user=None):
        # requests reuse the package-wide app context, so flask-login's cached
        # g._login_user would otherwise leak between clients and tests
        g.pop("_login_user", None)
        return application.test_client(user=user)

    yield make
    g.pop("_login_user", None)


@pytest.fixture
def no_csrf(application, monkeypatch):
    monkeypatch.setitem(application.config, "WTF_CSRF_ENABLED", False)


@pytest.fixture
def rank_settings(default_settings):
    Setting.install_group(SETTINGS.key)

    def update(**values):
        Setting.update(SETTINGS.key, values)

    return update


def _rank(name, requirement=None):
    return Rank.create(rank_name=name, rank_code=f"**{name}**", requirement=requirement)


def _give(user, rank):
    user.rank = rank
    db.session.commit()


def test_new_post_gives_highest_earned_rank(topic, user):
    _rank("Newbie", 1)
    regular = _rank("Regular", 2)
    _rank("Veteran", 10)

    Post(content="Test reply").save(user=user, topic=topic)

    assert Rank.of(user) is regular


def test_new_post_keeps_custom_rank(topic, user):
    hero = _rank("Hero")
    _rank("Newbie", 1)
    _give(user, hero)

    Post(content="Test reply").save(user=user, topic=topic)

    assert Rank.of(user) is hero


def test_guest_post_is_ignored(database):
    flaskbb_event_post_save_after(post=Post(content="Guest post"), is_new=True)


def test_overview_lists_ranks_users_and_nav_link(client, user):
    _rank("Newbie", 1)
    _give(user, _rank("Hero"))

    resp = client(user).get("/ranks/")

    assert resp.status_code == 200
    assert b"<strong>Newbie</strong>" in resp.data
    assert b"<strong>Hero</strong>" in resp.data
    assert f">{user.username}</a>".encode() in resp.data
    assert b'href="/ranks/"' in resp.data


def test_overview_hides_unapplied_custom_ranks(client, user):
    _rank("Hero")

    resp = client(user).get("/ranks/")

    assert b"<strong>Hero</strong>" not in resp.data
    assert b"???" in resp.data


def test_ranks_are_hidden_from_guests_unless_allowed(client, rank_settings):
    assert client().get("/ranks/").status_code == 302
    assert b'href="/ranks/"' not in client().get("/").data

    rank_settings(HIDE_FROM_GUESTS=False)

    assert client().get("/ranks/").status_code == 200
    assert b'href="/ranks/"' in client().get("/").data


def test_rank_detail_lists_users(client, user):
    hero = _rank("Hero")
    _give(user, hero)

    resp = client(user).get(f"/ranks/{hero.id}")

    assert resp.status_code == 200
    assert f">{user.username}</a>".encode() in resp.data


def test_hidden_rank_detail_is_only_visible_to_moderators(client, user, admin_user):
    hero = _rank("Hero")

    assert client(user).get(f"/ranks/{hero.id}").status_code == 404
    assert client(admin_user).get(f"/ranks/{hero.id}").status_code == 200


def test_topic_and_profile_show_rank(application, client, topic, user):
    _give(user, _rank("Hero"))
    with application.test_request_context():
        topic_url, profile_url = topic.url, user.url

    assert b"<strong>Hero</strong>" in client().get(topic_url).data
    assert b"<strong>Hero</strong>" in client().get(profile_url).data


def test_management_redirects_non_admins(client, user):
    assert client().get("/management/ranks/").status_code == 302
    assert client(user).get("/management/ranks/").status_code == 302


def test_admin_adds_and_edits_rank(client, admin_user, no_csrf):
    admin = client(admin_user)
    assert admin.get("/management/ranks/add").status_code == 200

    resp = admin.post(
        "/management/ranks/add",
        data={"rank_name": "Hero", "rank_code": "**Hero**", "requirement": ""},
    )
    assert resp.status_code == 302
    hero = Rank.get_by(rank_name="Hero")
    assert hero is not None and hero.is_custom()

    overview = admin.get("/management/ranks/")
    assert b"<strong>Hero</strong>" in overview.data
    assert b'href="/management/ranks/' in overview.data

    assert admin.get(f"/management/ranks/edit/{hero.id}").status_code == 200
    admin.post(
        f"/management/ranks/edit/{hero.id}",
        data={"rank_name": "Veteran", "rank_code": "*Veteran*", "requirement": "10"},
    )
    assert hero.rank_name == "Veteran"
    assert hero.requirement == 10


def test_admin_applies_and_deletes_custom_rank(client, admin_user, user, no_csrf):
    admin = client(admin_user)
    hero = _rank("Hero")

    assert admin.get(f"/management/ranks/apply/{hero.id}").status_code == 200
    resp = admin.post(f"/management/ranks/apply/{hero.id}", data={"username": "nobody"})
    assert b"No user with that username exists." in resp.data

    admin.post(f"/management/ranks/apply/{hero.id}", data={"username": user.username})
    assert Rank.of(user) is hero

    admin.post(f"/management/ranks/delete/{hero.id}")
    assert Rank.count() == 0
    assert Rank.of(user) is None


def test_requirement_ranks_cannot_be_applied(client, admin_user):
    newbie = _rank("Newbie", 1)

    assert client(admin_user).get(f"/management/ranks/apply/{newbie.id}").status_code == 404
