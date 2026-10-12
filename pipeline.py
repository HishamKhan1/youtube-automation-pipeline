import os
import json

from project import (
    load_video_info,
    get_completed_stories
)

from video import (
    generate_all_story_transitions,
    get_video_files_with_transitions,
    combine_story_videos,
    add_background_ambience
)

from metadata import (
    generate_youtube_metadata,
    save_youtube_metadata
)

from thumbnail import (
    generate_thumbnail_plan,
    save_thumbnail_plan,
    generate_thumbnail_image,
    create_final_thumbnail
)


def finalize_video_project(
    client,
    project_folder,
    rain_file
):

    print("\nFINALIZING VIDEO PROJECT...")

    # -------------------------
    # LOAD PROJECT INFORMATION
    # -------------------------

    video_info = load_video_info(
        project_folder
    )

    selected_stories = video_info[
        "selected_stories"
    ]

    story_count = len(
        selected_stories
    )

    completed_stories = get_completed_stories(
        project_folder,
        selected_stories
    )

    print(
        f"\nCOMPLETED STORIES: "
        f"{len(completed_stories)}"
    )

    # -------------------------
    # STORY TRANSITIONS
    # -------------------------

    generate_all_story_transitions(
        project_folder,
        selected_stories
    )

    # -------------------------
    # COMBINE STORY VIDEOS
    # -------------------------

    video_files = get_video_files_with_transitions(
        project_folder,
        story_count
    )

    concat_file = os.path.join(
        project_folder,
        "concat_with_transitions.txt"
    )

    transition_video = os.path.join(
        project_folder,
        "final_video_with_transitions.mp4"
    )

    combine_story_videos(
        video_files,
        transition_video,
        concat_file
    )

    # -------------------------
    # ADD RAIN AMBIENCE
    # -------------------------

    final_video = os.path.join(
        project_folder,
        "final_video_complete.mp4"
    )

    add_background_ambience(
        transition_video,
        rain_file,
        final_video
    )

    # -------------------------
    # YOUTUBE METADATA
    # -------------------------

    metadata_file = os.path.join(
        project_folder,
        "youtube_metadata.json"
    )

    if os.path.exists(metadata_file):

        with open(
            metadata_file,
            "r",
            encoding="utf-8"
        ) as f:
            metadata = json.load(f)

        print(
            "YOUTUBE METADATA ALREADY EXISTS "
            "- USING SAVED VERSION"
        )

    else:

        metadata = generate_youtube_metadata(
            client,
            video_info["video_idea"],
            completed_stories
        )

        save_youtube_metadata(
            project_folder,
            metadata
        )

    # -------------------------
    # THUMBNAIL PLAN
    # -------------------------

    thumbnail_plan_file = os.path.join(
        project_folder,
        "thumbnail_plan.json"
    )

    if os.path.exists(
        thumbnail_plan_file
    ):

        with open(
            thumbnail_plan_file,
            "r",
            encoding="utf-8"
        ) as f:
            thumbnail_plan = json.load(f)

        print(
            "THUMBNAIL PLAN ALREADY EXISTS "
            "- USING SAVED VERSION"
        )

    else:

        thumbnail_plan = generate_thumbnail_plan(
            client,
            metadata,
            completed_stories
        )

        save_thumbnail_plan(
            project_folder,
            thumbnail_plan
        )

    # -------------------------
    # THUMBNAIL BACKGROUND
    # -------------------------

    thumbnail_background = os.path.join(
        project_folder,
        "thumbnail_background.png"
    )

    if not os.path.exists(
        thumbnail_background
    ):

        generate_thumbnail_image(
            client,
            project_folder,
            thumbnail_plan
        )

    else:

        print(
            "THUMBNAIL BACKGROUND ALREADY EXISTS "
            "- SKIPPING IMAGE GENERATION"
        )

    # -------------------------
    # FINAL THUMBNAIL
    # -------------------------

    create_final_thumbnail(
        project_folder,
        thumbnail_plan
    )

    # -------------------------
    # COMPLETE
    # -------------------------

    print("\nPROJECT COMPLETE")
    print(
        f"VIDEO: {final_video}"
    )
    print(
        f"METADATA: {metadata_file}"
    )
    print(
        "THUMBNAIL: "
        f"{os.path.join(project_folder, 'thumbnail_final.png')}"
    )