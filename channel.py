import os
import json


def validate_channel_config(
    channel_config,
    expected_slug=None
):

    if not isinstance(
        channel_config,
        dict
    ):
        raise ValueError(
            "Channel config must be a JSON object."
        )

    required_fields = [
        "name",
        "slug",
        "content_type",
        "voice_id",
        "background_file",
        "ambience_file",
        "story_count",
        "story_length",
        "thumbnail_style",
        "formats"
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in channel_config
    ]

    if missing_fields:
        raise ValueError(
            f"Channel config is missing fields: "
            f"{missing_fields}"
        )

    for section in [
        "story_count",
        "story_length",
        "formats"
    ]:
        if not isinstance(
            channel_config[section],
            dict
        ):
            raise ValueError(
                f"Channel config '{section}' "
                f"must be an object."
            )

    for field in [
        "minimum",
        "maximum"
    ]:
        if field not in channel_config["story_count"]:
            raise ValueError(
                f"Channel config 'story_count' "
                f"is missing '{field}'."
            )

    for field in [
        "minimum_words",
        "maximum_words"
    ]:
        if field not in channel_config["story_length"]:
            raise ValueError(
                f"Channel config 'story_length' "
                f"is missing '{field}'."
            )

        story_minimum = channel_config[
            "story_count"
        ]["minimum"]

        story_maximum = channel_config[
            "story_count"
        ]["maximum"]

        word_minimum = channel_config[
            "story_length"
        ]["minimum_words"]

        word_maximum = channel_config[
            "story_length"
        ]["maximum_words"]

        for value in [
            story_minimum,
            story_maximum,
            word_minimum,
            word_maximum
        ]:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value <= 0
            ):
                raise ValueError(
                    "Story count and story length "
                    "values must be positive integers."
                )

        if story_minimum > story_maximum:
            raise ValueError(
                "story_count minimum cannot be "
                "greater than maximum."
            )

        if word_minimum > word_maximum:
            raise ValueError(
                "story_length minimum_words cannot be "
                "greater than maximum_words."
            )

        for field in [
            "longform",
            "shorts"
        ]:
            if field not in channel_config["formats"]:
                raise ValueError(
                    f"Channel config 'formats' "
                    f"is missing '{field}'."
                )

            if not isinstance(
                channel_config["formats"][field],
                bool
            ):
                raise ValueError(
                    f"Channel config 'formats.{field}' "
                    f"must be true or false."
                )

        for field in [
            "name",
            "slug",
            "content_type",
            "voice_id",
            "background_file",
            "ambience_file",
            "thumbnail_style"
        ]:
            value = channel_config[field]

            if (
                not isinstance(value, str)
                or not value.strip()
            ):
                raise ValueError(
                    f"Channel config '{field}' "
                    f"must be a non-empty string."
                )

        if (
            expected_slug is not None
            and channel_config["slug"] != expected_slug
        ):
            raise ValueError(
                f"Channel config slug "
                f"'{channel_config['slug']}' "
                f"does not match folder "
                f"'{expected_slug}'."
            )

        return True

def validate_channel_assets(
    channel_config
):

    asset_fields = [
        "background_file",
        "ambience_file"
    ]

    for field in asset_fields:

        file_path = channel_config[
            field
        ]

        if not os.path.isfile(
            file_path
        ):
            raise FileNotFoundError(
                f"Channel asset not found for "
                f"'{field}': {file_path}"
            )

    return True

def load_channel_config(
    channel_slug
):

    config_path = os.path.join(
        "channels",
        channel_slug,
        "channel.json"
    )

    if not os.path.exists(
        config_path
    ):

        raise FileNotFoundError(
            f"Channel config not found: "
            f"{config_path}"
        )

    with open(
        config_path,
        "r",
        encoding="utf-8"
    ) as file:

        channel_config = json.load(
            file
        )

    validate_channel_config(
        channel_config,
        expected_slug=channel_slug
    )

    return channel_config

def get_available_channels():

    channels_folder = "channels"

    if not os.path.exists(
        channels_folder
    ):
        return []

    channels = []

    for folder_name in os.listdir(
        channels_folder
    ):

        config_path = os.path.join(
            channels_folder,
            folder_name,
            "channel.json"
        )

        if os.path.isfile(
            config_path
        ):
            channels.append(
                folder_name
            )

    return sorted(
        channels
    )

def choose_channel():

    available_channels = get_available_channels()

    if not available_channels:

        raise RuntimeError(
            "No channel configs found."
        )

    print("\nCHOOSE CHANNEL")

    for index, channel_slug in enumerate(
        available_channels,
        start=1
    ):

        config = load_channel_config(
            channel_slug
        )

        print(
            f"{index}. {config['name']}"
        )

    channel_choice = input(
        "\nChoose a channel: "
    )

    try:

        channel_index = int(
            channel_choice
        ) - 1

        selected_channel_slug = (
            available_channels[
                channel_index
            ]
        )

    except (
        ValueError,
        IndexError
    ):

        raise RuntimeError(
            "Invalid channel selection."
        )

    channel_config = load_channel_config(
        selected_channel_slug
    )

    validate_channel_assets(
        channel_config
    )

    return (
        selected_channel_slug,
        channel_config
    )

def save_project_channel_config(
    project_folder,
    channel_config
):

    config_path = os.path.join(
        project_folder,
        "channel_config.json"
    )

    with open(
        config_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            channel_config,
            file,
            indent=4
        )

    print(
        f"PROJECT CHANNEL CONFIG SAVED: "
        f"{config_path}"
    )

def load_project_channel_config(
    project_folder
):

    config_path = os.path.join(
        project_folder,
        "channel_config.json"
    )

    if not os.path.exists(
        config_path
    ):
        return None

    with open(
        config_path,
        "r",
        encoding="utf-8"
    ) as file:

        channel_config = json.load(
            file
        )

    validate_channel_config(
        channel_config
    )

    return channel_config

def resolve_project_channel_config(
    project_folder,
    video_info
):

    channel_config = load_project_channel_config(
        project_folder
    )

    if channel_config is not None:

        validate_channel_assets(
            channel_config
        )

        return (
            channel_config["slug"],
            channel_config
        )

    selected_channel_slug = video_info.get(
        "channel_slug"
    )

    if not selected_channel_slug:

        selected_channel_slug = (
            "after_dark_archive"
        )

    channel_config = load_channel_config(
        selected_channel_slug
    )

    validate_channel_assets(
        channel_config
    )

    return (
        selected_channel_slug,
        channel_config
    )









