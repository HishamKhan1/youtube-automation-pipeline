import os
import json


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

        return json.load(file)

def resolve_project_channel_config(
    project_folder,
    video_info
):

    channel_config = load_project_channel_config(
        project_folder
    )

    if channel_config is not None:

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

    return (
        selected_channel_slug,
        channel_config
    )









