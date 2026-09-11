import pytest
from flaskbb.extensions import pluggy
from flaskbb.settings import setting_registry
from tests.fixtures.app import *
from tests.fixtures.forum import *
from tests.fixtures.user import *

import flaskbb_ranks
from flaskbb_ranks.settings import SETTINGS
from flaskbb_ranks.views import ranks, ranks_management


@pytest.fixture(scope="package", autouse=True)
def _register_ranks(application):
    """Normally done by create_app() for an entry-point installed plugin."""
    if "ranks" not in application.blueprints:
        application.register_blueprint(ranks, url_prefix="/ranks")
        application.register_blueprint(ranks_management, url_prefix="/management/ranks")
    if not pluggy.is_registered(flaskbb_ranks):
        pluggy.register(flaskbb_ranks, name="ranks")
    if not setting_registry.is_plugin_group(SETTINGS.key):
        setting_registry.register_group(SETTINGS, is_plugin=True)
