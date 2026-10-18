import os
import json
from cost_tracking import print_cost_summary
from state import (
    run_stage,
    mark_project_complete,
    complete_stage_if_file_exists
)
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
    # RECOGNIZE EXISTING OUTPUTS
    # -------------------------

    existing_final_video = os.path.join(
        project_folder,
        "final_video_complete.mp4"
    )

    if os.path.exists(
        existing_final_video
    ):

        complete_stage_if_file_exists(
            project_folder,
            "transitions",
            existing_final_video
        )

        complete_stage_if_file_exists(
            project_folder,
            "combined_video",
            existing_final_video
        )

        complete_stage_if_file_exists(
            project_folder,
            "ambience",
            existing_final_video
        )

    complete_stage_if_file_exists(
        project_folder,
        "metadata",
        os.path.join(
            project_folder,
            "youtube_metadata.json"
        )
    )

    complete_stage_if_file_exists(
        project_folder,
        "thumbnail_plan",
        os.path.join(
            project_folder,
            "thumbnail_plan.json"
        )
    )

    complete_stage_if_file_exists(
        project_folder,
        "thumbnail_image",
        os.path.join(
            project_folder,
            "thumbnail_background.png"
        )
    )

    complete_stage_if_file_exists(
        project_folder,
        "thumbnail_final",
        os.path.join(
            project_folder,
            "thumbnail_final.png"
        )
    )

    # -------------------------
    # STORY TRANSITIONS
    # -------------------------

    run_stage(
        project_folder,
        "transitions",
        generate_all_story_transitions,
        project_folder,
        selected_stories
    )

    # -------------------------
    # COMBINE STORY VIDEOS
    # -------------------------

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

    run_stage(
        project_folder,
        "combined_video",
        combine_story_videos,
        video_files,
        concat_file,
        transition_video
    )

    # -------------------------
    # ADD RAIN AMBIENCE
    # -------------------------

    final_video = os.path.join(
        project_folder,
        "final_video_complete.mp4"
    )

    run_stage(
        project_folder,
        "ambience",
        add_background_ambience,
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

    def prepare_metadata():

        if os.path.exists(metadata_file):

            print(
                "\nYOUTUBE METADATA ALREADY EXISTS "
                "- USING SAVED VERSION"
            )

            with open(
                metadata_file,
                "r",
                encoding="utf-8"
            ) as file:

                return json.load(file)

        metadata = generate_youtube_metadata(
            client,
            project_folder,
            video_info["video_idea"],
            completed_stories
        )

        save_youtube_metadata(
            project_folder,
            metadata
        )

        return metadata

    metadata = run_stage(
        project_folder,
        "metadata",
        prepare_metadata,
        on_skip=prepare_metadata
    )
    
    # -------------------------
    # THUMBNAIL PLAN
    # -------------------------

    thumbnail_plan_file = os.path.join(
        project_folder,
        "thumbnail_plan.json"
    )

    def prepare_thumbnail_plan():

        if os.path.exists(
            thumbnail_plan_file
        ):

            print(
                "\nTHUMBNAIL PLAN ALREADY EXISTS "
                "- USING SAVED VERSION"
            )

            with open(
                thumbnail_plan_file,
                "r",
                encoding="utf-8"
            ) as file:

                return json.load(file)

        thumbnail_plan = generate_thumbnail_plan(
            client,
            project_folder,
            metadata,
            completed_stories
        )

        save_thumbnail_plan(
            project_folder,
            thumbnail_plan
        )

        return thumbnail_plan

    thumbnail_plan = run_stage(
        project_folder,
        "thumbnail_plan",
        prepare_thumbnail_plan,
        on_skip=prepare_thumbnail_plan
    )

    # -------------------------
    # THUMBNAIL BACKGROUND
    # -------------------------

    # -------------------------
    # THUMBNAIL BACKGROUND
    # -------------------------

    thumbnail_background = os.path.join(
        project_folder,
        "thumbnail_background.png"
    )

    def prepare_thumbnail_image():

        if os.path.exists(
            thumbnail_background
        ):

            print(
                "\nTHUMBNAIL BACKGROUND ALREADY EXISTS "
                "- SKIPPING IMAGE GENERATION"
            )

            return

        generate_thumbnail_image(
            client,
            project_folder,
            thumbnail_plan
        )

    run_stage(
        project_folder,
        "thumbnail_image",
        prepare_thumbnail_image,
        skip_if_complete=False
    )

    # -------------------------
    # FINAL THUMBNAIL
    # -------------------------

    # -------------------------
    # FINAL THUMBNAIL
    # -------------------------

    run_stage(
        project_folder,
        "thumbnail_final",
        create_final_thumbnail,
        project_folder,
        thumbnail_plan
    )

    # -------------------------
    # COMPLETE
    # -------------------------

    mark_project_complete(
        project_folder
    )

    print_cost_summary(
        project_folder
    )

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