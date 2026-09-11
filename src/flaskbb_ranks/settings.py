from flaskbb.settings import BoolSetting, flaskbb_config, IntSetting, SettingGroup, StringSetting

SETTINGS = SettingGroup(
    key="ranks",
    name="Ranks",
    description="Settings for the public rank overview and rank details.",
    settings=(
        BoolSetting(
            key="HIDE_FROM_GUESTS",
            value=True,
            name="Hide ranks from guests",
            description="Hides the rank overview and rank details from guests.",
        ),
        BoolSetting(
            key="HIDE_UNAPPLIED_RANKS",
            value=False,
            name="Hide unapplied ranks",
            description=(
                "Replaces post count ranks that nobody holds with placeholders in the overview."
            ),
        ),
        StringSetting(
            key="NAME_PLACEHOLDER",
            value="???",
            name="Rank name placeholder",
            description="Shown instead of the name of a hidden rank.",
        ),
        StringSetting(
            key="CODE_PLACEHOLDER",
            value="???",
            name="Rank display placeholder",
            description="Shown instead of the display of a hidden rank. May be markdown.",
        ),
        StringSetting(
            key="REQUIREMENT_PLACEHOLDER",
            value="???",
            name="Rank requirement placeholder",
            description=(
                "Shown instead of the post requirement of a hidden rank. "
                "Leave empty to show the requirement."
            ),
        ),
        BoolSetting(
            key="HIDE_UNAPPLIED_CUSTOM_RANKS",
            value=True,
            name="Hide unapplied custom ranks",
            description=(
                "Replaces custom ranks that nobody holds with placeholders in the overview."
            ),
        ),
        StringSetting(
            key="CUSTOM_NAME_PLACEHOLDER",
            value="???",
            name="Custom rank name placeholder",
            description=(
                "Shown instead of the name of a hidden custom rank. "
                "Leave empty to use the rank name placeholder."
            ),
        ),
        StringSetting(
            key="CUSTOM_CODE_PLACEHOLDER",
            value="???",
            name="Custom rank display placeholder",
            description=(
                "Shown instead of the display of a hidden custom rank. May be markdown. "
                "Leave empty to use the rank display placeholder."
            ),
        ),
        BoolSetting(
            key="SHOW_USERS",
            value=True,
            name="Show users with a rank",
            description="Lists the users holding a rank in the overview and on the rank details.",
        ),
        IntSetting(
            key="HOW_MANY_USERS",
            value=5,
            min=1,
            name="Users per rank in the overview",
            description=(
                "How many users are listed per rank in the overview. "
                "The rank details list all of them."
            ),
        ),
    ),
)

_DEFAULTS = {setting.key: setting.value for setting in SETTINGS.settings}


def rank_setting(key: str):
    return flaskbb_config.get(f"{SETTINGS.key.upper()}_{key}", _DEFAULTS[key])
