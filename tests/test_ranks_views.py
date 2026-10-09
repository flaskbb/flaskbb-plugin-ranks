import pytest
from flask import g
from flask_login.test_client import FlaskLoginClient
from flaskbb.extensions import db
from flaskbb.forum.models import Post
from flaskbb.settings import Setting
from flaskbb.user.models import User
from sqlalchemy import event

import flaskbb_ranks
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
        g.pop("_ranks_in_post", None)
        return application.test_client(user=user)

    yield make
    g.pop("_login_user", None)
    g.pop("_ranks_in_post", None)


@pytest.fixture
def queries():
    """Records every SQL statement, so tests can count the queries a request makes."""
    statements = []

    def record(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(db.engine, "before_cursor_execute", record)
    yield statements
    event.remove(db.engine, "before_cursor_execute", record)


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


def _user(default_groups, name):
    return User(
        username=name,
        email=f"{name}@example.org",
        password="test",
        primary_group=default_groups[3],
        activated=True,
    ).save()


def _measure(client, url, queries):
    """Rank queries of a repeat visit, with the session emptied like at the start of a request."""
    client.get(url)
    db.session.expire_all()
    queries.clear()
    resp = client.get(url)
    assert resp.status_code == 200
    return resp, sum(1 for statement in queries if "rank" in statement)


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


def test_overview_shows_the_first_users_and_links_to_the_rest(client, user, default_groups):
    hero = _rank("Hero")
    _give(user, hero)
    for i in range(6):
        _give(_user(default_groups, f"holder{i}"), hero)

    resp = client(user).get("/ranks/")

    assert f">{user.username}</a>".encode() in resp.data
    assert b">holder3</a>" in resp.data
    assert b">holder4</a>" not in resp.data
    assert f'href="/ranks/{hero.id}">more</a>'.encode() in resp.data


def test_overview_without_shown_users_still_hides_unapplied_ranks(
    client, user, default_groups, rank_settings
):
    _give(_user(default_groups, "holder"), _rank("Hero"))
    _rank("Ghost")
    rank_settings(SHOW_USERS=False)

    resp = client(user).get("/ranks/")

    assert b"<strong>Hero</strong>" in resp.data
    assert b">holder</a>" not in resp.data
    assert b"<strong>Ghost</strong>" not in resp.data


def test_rank_pages_query_count_does_not_grow_with_users(client, user, default_groups, queries):
    hero = _rank("Hero")
    _give(user, hero)
    viewer = client(user)
    _, overview_queries = _measure(viewer, "/ranks/", queries)
    _, detail_queries = _measure(viewer, f"/ranks/{hero.id}", queries)

    for i in range(12):
        _give(_user(default_groups, f"holder{i}"), hero)

    overview, overview_queries_now = _measure(viewer, "/ranks/", queries)
    detail, detail_queries_now = _measure(viewer, f"/ranks/{hero.id}", queries)

    assert overview_queries_now == overview_queries
    assert detail_queries_now == detail_queries
    assert b">holder11</a>" not in overview.data
    assert b">holder11</a>" in detail.data


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


def test_topic_renders_each_rank_once(application, client, topic, user, default_groups, mocker):
    hero = _rank("Hero")
    _give(user, hero)
    for i in range(4):
        holder = _user(default_groups, f"holder{i}")
        _give(holder, hero)
        Post(content=f"reply {i}").save(user=holder, topic=topic)
    with application.test_request_context():
        topic_url = topic.url
    render = mocker.spy(flaskbb_ranks, "render_template")

    resp = client(user).get(topic_url)

    assert resp.data.count(b"<strong>Hero</strong>") == 5
    assert render.call_count == 1


def test_topic_query_count_does_not_grow_with_posts(
    application, client, topic, user, default_groups, queries
):
    hero = _rank("Hero")
    _give(user, hero)
    with application.test_request_context():
        topic_url = topic.url
    viewer = client(user)

    def reply(name):
        holder = _user(default_groups, name)
        _give(holder, hero)
        Post(content=f"reply by {name}").save(user=holder, topic=topic)

    reply("holder0")
    _, with_two_posts = _measure(viewer, topic_url, queries)
    for i in range(1, 5):
        reply(f"holder{i}")
    _, with_six_posts = _measure(viewer, topic_url, queries)

    assert with_six_posts == with_two_posts


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
