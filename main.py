# Hisham Khan 
# Start Date 2026-09-28
# Last update 2026-10-12
# Youtube Video Generator
"""
reddit-video-generator/
│
├── main.py
├── config.py
│
├── modules/
│   ├── idea_generator.py
│   ├── reddit_finder.py
│   ├── story_selector.py
│   ├── script_writer.py
│   ├── narrator.py
│   ├── visual_generator.py
│   ├── video_editor.py
│   └── file_manager.py
│
├── assets/
│   ├── music/
│   ├── fonts/
│   └── backgrounds/
│
└── output/
    └── 2026-09-28_10_scariest_reddit_stories/
        ├── stories/
        ├── scripts/
        ├── audio/
        ├── visuals/
        ├── metadata.json
        └── final_video.mp4
"""

import os
from dotenv import load_dotenv
from openai import OpenAI
from elevenlabs.client import ElevenLabs
from cost_tracking import flush_pending_cost_events
from channel import (
    choose_channel,
    save_project_channel_config,
    resolve_project_channel_config
)

from audio import (
    generate_all_story_audio,
    all_story_audio_is_valid
)
from subtitles import (
    generate_all_story_subtitles,
    generate_all_subtitled_videos,
    all_story_subtitles_are_valid,
    all_subtitled_videos_are_valid
)

from video import (
    generate_all_story_videos,
    generate_all_visual_story_videos,
    all_story_videos_are_valid
)

from visuals import (
    generate_all_visual_plans,
    all_visual_plans_are_valid,
    generate_all_scene_images,
    all_scene_images_are_valid
)

from story_generation import (
    generate_idea,
    generate_story_ideas,
    select_best_stories,
    prepare_premise,
    get_replacement_story,
    generate_narrator_profile,
    generate_full_story,
    prepare_story
)
from project import (
    save_video_info,
    load_video_info,
    choose_project_folder,
    completed_story_files_are_valid
)
from state import (
    create_project_state,
    load_project_state,
    set_stage_status,
    run_stage,
    complete_stage_if_file_exists
)

from pipeline import finalize_video_project

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

elevenlabs = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY")
)



print("\nYOUTUBE VIDEO GENERATOR")

print("\n1. Create new video")
print("2. Resume existing video")
print("3. Finalize video")

choice = input("\nChoose an option: ")


# -----------------------------------
# CREATE NEW VIDEO
# -----------------------------------

if choice == "1":

    print("\nCREATING NEW VIDEO...")

    selected_channel_slug, channel_config = choose_channel()

    print(
        f"\nCHANNEL: "
        f"{channel_config['name']}"
    )
    
    idea = generate_idea(
        client,
        channel_config["story_count"]["minimum"],
        channel_config["story_count"]["maximum"]
    )

    print("\nVIDEO IDEA:")
    print(idea)

    story_ideas = generate_story_ideas(client, idea)

    print("\nGENERATED STORY IDEAS:")
    for story in story_ideas["stories"]:
        print(
            story["id"],
            "-",
            story["title"]
        )

    selected_ids = select_best_stories(
        client,
        idea,
        story_ideas
    )

    expected_story_count = idea[
        "story_count"
    ]

    if len(selected_ids) != expected_story_count:

        raise RuntimeError(
            f"Story selection returned "
            f"{len(selected_ids)} stories, "
            f"but {expected_story_count} were requested."
        )
    
    available_story_ids = {
        story["id"]
        for story in story_ideas["stories"]
    }

    invalid_selected_ids = [
        story_id
        for story_id in selected_ids
        if story_id not in available_story_ids
    ]

    if invalid_selected_ids:

        raise RuntimeError(
            f"Story selection returned invalid IDs: "
            f"{invalid_selected_ids}"
        )
    
    selected_stories = [
        story
        for story in story_ideas["stories"]
        if story["id"] in selected_ids
    ]
    
    all_story_ideas = story_ideas["stories"]

    attempted_story_ids = set()
    narrator_profiles = {}
    
    print("\nSELECTED STORIES:")
    for story in selected_stories:
        print(
            story["id"],
            "-",
            story["title"]
        )


    # Create folder name from video title

    folder_name = idea["title"].lower()

    folder_name = "".join(
        char if char.isalnum() or char in " _-" else ""
        for char in folder_name
    )

    folder_name = folder_name.replace(" ", "_")

    output_folder = os.path.join(
        "output",
        folder_name
    )

    os.makedirs(
        output_folder,
        exist_ok=True
    )
    flush_pending_cost_events(
        output_folder
    )
    save_project_channel_config(
        output_folder,
        channel_config
    )
    create_project_state(
        output_folder
    )
    set_stage_status(
        output_folder,
        "idea",
        "complete"
    )
    set_stage_status(
        output_folder,
        "story_selection",
        "complete"
    )


    # Save project information

    save_video_info(
        output_folder,
        idea,
        selected_stories,
        all_story_ideas,
        channel_slug=channel_config["slug"]
    )

    print(
        f"\nPROJECT SAVED: {output_folder}"
    )


# -----------------------------------
# RESUME EXISTING VIDEO
# -----------------------------------

elif choice == "2":

    print("\nRESUME VIDEO")

    folder_name = input(
        "Enter the project folder name: "
    )

    output_folder = os.path.join(
        "output",
        folder_name
    )

    video_info = load_video_info(
        output_folder
    )

    if video_info is None:

        print("\nProject not found.")
        print("Check the folder name and try again.")

        exit()

    selected_channel_slug, channel_config = (
        resolve_project_channel_config(
            output_folder,
            video_info
        )
    )
    print(
        f"\nCHANNEL: "
        f"{channel_config['name']}"
    )
    
    project_state = load_project_state(
        output_folder
    )

    idea = video_info["video_idea"]

    selected_stories = video_info["selected_stories"]

    all_story_ideas = video_info.get(
    "all_story_ideas",
    selected_stories)
    
    attempted_story_ids = set(
    video_info.get(
        "attempted_story_ids",
        []
        )   
    )
    
    narrator_profiles = video_info.get(
    "narrator_profiles",
    {}
    )   
    
    print("\nPROJECT LOADED:")
    print(idea["title"])

    print(
        f"Stories planned: {len(selected_stories)}"
    )

elif choice == "3":

    project_folder = choose_project_folder()

    if project_folder:

        video_info = load_video_info(
            project_folder
        )

        if video_info is None:

            print(
                "\nProject information "
                "could not be loaded."
            )

            raise SystemExit

        selected_channel_slug, channel_config = (
            resolve_project_channel_config(
                project_folder,
                video_info
            )
        )

        print(
            f"\nCHANNEL: "
            f"{channel_config['name']}"
        )

        rain_file = channel_config[
            "ambience_file"
        ]

        finalize_video_project(
            client,
            project_folder,
            rain_file
        )

        raise SystemExit
        
# -----------------------------------
# INVALID OPTION
# -----------------------------------

else:

    print("\nInvalid option.")
    exit()

def generate_project_stories(
    client,
    output_folder,
    idea,
    selected_stories,
    all_story_ideas,
    attempted_story_ids,
    narrator_profiles,
    channel_config
):
    previous_stories = []

    for number, story_idea in enumerate(selected_stories, start=1):

        file_name = f"story_{number:02d}.txt"
        draft_file_name = f"story_{number:02d}_draft.txt"

        file_path = os.path.join(
            output_folder,
            file_name
        )

        draft_file_path = os.path.join(
            output_folder,
            draft_file_name
        )

        # -----------------------------------
        # FINAL STORY ALREADY EXISTS
        # -----------------------------------

        if os.path.exists(file_path):

            print(
                f"\nSTORY {number} ALREADY EXISTS - SKIPPING"
            )

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as file:
                existing_story = file.read()

            previous_stories.append(existing_story)
            
            attempted_story_ids.add(
                story_idea["id"]
            )
            
            continue


    # -----------------------------------
    # CHECK / REPAIR PREMISE
    # -----------------------------------

        print(
            f"\nPREPARING STORY "
            f"{number}/{len(selected_stories)}"
        )

        current_story_idea = story_idea


        while True:

            attempted_story_ids.add(
                current_story_idea["id"]
            )

            save_video_info(
                output_folder,
                idea,
                selected_stories,
                all_story_ideas,
                attempted_story_ids,
                narrator_profiles,
            channel_slug=channel_config["slug"]
            )

            prepared_story_idea = prepare_premise(
                client,
                output_folder,
                idea,
                story_idea
            )

            if prepared_story_idea is not None:

                break

            print(
                f"\nPREMISE FAILED: "
                f"{current_story_idea['title']}"
            )

            replacement = get_replacement_story(
                client,
                output_folder,
                idea,
                all_story_ideas,
                selected_stories,
                attempted_story_ids
            )

            if replacement is None:

                print(
                    "\nNO REPLACEMENT PREMISES AVAILABLE"
                )

                prepared_story_idea = None

                break

            print(
                f"\nTRYING REPLACEMENT: "
                f"{replacement['title']}"
            )

            current_story_idea = replacement


        if prepared_story_idea is None:

            print(
                f"\nCOULD NOT COMPLETE STORY {number}"
            )

            continue
        
        selected_stories[number - 1] = prepared_story_idea

        save_video_info(
            output_folder,
            idea,
            selected_stories,
            all_story_ideas,
            attempted_story_ids,
            narrator_profiles,
            channel_slug=channel_config["slug"]
        )

        # -----------------------------------
        # LOAD OR GENERATE DRAFT
        # -----------------------------------

        profile_key = str(number)

        if profile_key in narrator_profiles:

            narrator_profile = narrator_profiles[
                profile_key
            ]

            print("\nUSING SAVED NARRATOR PROFILE:")
            print(narrator_profile)

        else:

            narrator_profile = generate_narrator_profile(
                client,
                output_folder,
                idea,
                prepared_story_idea
            )

            narrator_profiles[
                profile_key
            ] = narrator_profile

            save_video_info(
                output_folder,
                idea,
                selected_stories,
                all_story_ideas,
                attempted_story_ids,
                narrator_profiles,
                channel_slug=channel_config["slug"]
            )

            print("\nNEW NARRATOR PROFILE:")
            print(narrator_profile)
        
        if os.path.exists(draft_file_path):

            print(
                f"\nDRAFT FOR STORY {number} "
                f"ALREADY EXISTS - LOADING"
            )

            with open(
                draft_file_path,
                "r",
                encoding="utf-8"
            ) as file:
                draft = file.read()

        else:

            print(
                f"\nGENERATING STORY "
                f"{number}/{len(selected_stories)}"
            )

            print(
                prepared_story_idea["title"]
            )

            draft = generate_full_story(
                client,
                output_folder,
                idea,
                prepared_story_idea,
                narrator_profile,
                channel_config["story_length"]["minimum_words"],
                channel_config["story_length"]["maximum_words"]
            )

            with open(
                draft_file_path,
                "w",
                encoding="utf-8"
            ) as file:
                file.write(draft)

            print(
                f"SAVED DRAFT: "
                f"{draft_file_path}"
            )


        # -----------------------------------
        # QUALITY CONTROL
        # -----------------------------------

        print(
            f"\nQUALITY CHECKING STORY {number}..."
        )
        
        final_story = prepare_story(
            client,
            output_folder,
            idea,
            prepared_story_idea,
            draft
        )
        
        if final_story is None:

            print(
                f"\nSTORY {number} FAILED QUALITY CONTROL"
            )

            if os.path.exists(draft_file_path):
                os.remove(draft_file_path)

            continue


        # -----------------------------------
        # SAVE FINAL STORY
        # -----------------------------------

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as file:
            file.write(final_story)

        previous_stories.append(final_story)

        print(
            f"SAVED FINAL STORY: "
            f"{file_path}"
        )


    print("\nALL AVAILABLE STORIES COMPLETE!")

    stories_complete_marker = os.path.join(
        output_folder,
        "stories_complete.marker"
    )

    with open(
        stories_complete_marker,
        "w",
        encoding="utf-8"
    ) as file:
        file.write("complete")


# # Generate, review, and save every selected story

# -----------------------------------
# RECOGNIZE ALREADY-FINISHED PROJECT
# -----------------------------------

existing_final_video = os.path.join(
    output_folder,
    "final_video_complete.mp4"
)

if os.path.exists(
    existing_final_video
):

    for stage in [
        "stories",
        "audio",
        "subtitles",
        "story_videos",
        "subtitled_videos"
    ]:

        complete_stage_if_file_exists(
            output_folder,
            stage,
            existing_final_video
        )

run_stage(
    output_folder,
    "stories",
    generate_project_stories,
    client,
    output_folder,
    idea,
    selected_stories,
    all_story_ideas,
    attempted_story_ids,
    narrator_profiles,
    channel_config,
    completion_check=lambda: completed_story_files_are_valid(
        output_folder,
        selected_stories
    )
)

run_stage(
    output_folder,
    "audio",
    generate_all_story_audio,
    elevenlabs,
    output_folder,
    len(selected_stories),
    channel_config["voice_id"],
    completion_check=lambda: all_story_audio_is_valid(
        output_folder,
        len(selected_stories)
    )
)

run_stage(
    output_folder,
    "subtitles",
    generate_all_story_subtitles,
    client,
    output_folder,
    len(selected_stories),
    completion_check=lambda: all_story_subtitles_are_valid(
        output_folder,
        len(selected_stories)
    )
)

if not os.path.exists(
    existing_final_video
):

    run_stage(
        output_folder,
        "visual_plans",
        generate_all_visual_plans,
        client,
        output_folder,
        idea,
        selected_stories,
        narrator_profiles,
        completion_check=lambda: all_visual_plans_are_valid(
            output_folder,
            selected_stories
        )
    )

    run_stage(
    output_folder,
    "scene_images",
    generate_all_scene_images,
    client,
    output_folder,
    selected_stories,
    completion_check=lambda: all_scene_images_are_valid(
        output_folder,
        selected_stories
    )
)
background_file = channel_config[
    "background_file"
]

if not os.path.exists(
    existing_final_video
):

    run_stage(
        output_folder,
        "story_videos",
        generate_all_visual_story_videos,
        output_folder,
        len(selected_stories),
        completion_check=lambda: all_story_videos_are_valid(
            output_folder,
            len(selected_stories)
        )
    )

run_stage(
    output_folder,
    "subtitled_videos",
    generate_all_subtitled_videos,
    output_folder,
    len(selected_stories),
    completion_check=lambda: all_subtitled_videos_are_valid(
        output_folder,
        len(selected_stories)
    )
)