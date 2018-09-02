from flask import _request_ctx_stack, has_request_context
from werkzeug.datastructures import ImmutableDict
from werkzeug.local import LocalProxy

from flaskbb.plugins.models import PluginRegistry


def _get_rank_settings():
    plugin = PluginRegistry.query.filter_by(name="ranks").first()
    if plugin is None:
        return ImmutableDict()

    rank_settings = {
        "hide": plugin.settings.get("hide_unapplied_ranks", False),
        "hide_custom": plugin.settings.get("hide_unapplied_custom_ranks", True),
        "name": plugin.settings.get("rank_name_placeholder", "???"),
        "requirement": plugin.settings.get("rank_requirement_placeholder", "???"),
        "code": plugin.settings.get("rank_code_placeholder", "???"),
        "show_users": plugin.settings.get("show_users_for_ranks", True),
        "how_many_users": plugin.settings.get("how_many_users", 5),
        "hide_from_guests": plugin.settings.get("hide_from_guests", True),
    }

    rank_settings["custom_name"] = plugin.settings.get(
        "rank_custom_name_placeholder", rank_settings["name"]
    )
    rank_settings["custom_code"] = plugin.settings.get(
        "rank_custom_code_placeholder", rank_settings["code"]
    )

    return ImmutableDict(rank_settings)


@LocalProxy
def rank_settings():
    if (
        has_request_context()
        and getattr(_request_ctx_stack.top, "rank_settings", None) is None
    ):
        _request_ctx_stack.top.rank_settings = _get_rank_settings()
    return getattr(_request_ctx_stack.top, "rank_settings", ImmutableDict())
