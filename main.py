# Hisham Khan 
# Start Date 2026-09-28
# Last update 2026-09-29
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

from audio import (
    generate_all_story_audio
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
    choose_project_folder
)
from pipeline import finalize_video_project

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

elevenlabs = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY")
)


#### These Functions Create and revise our video scripts <
#--------------------------------------------------------------

#### These Functions create the video 




#### These Functions create the video







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

    idea = generate_idea()

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
        idea,
        story_ideas
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


    # Save project information

    save_video_info(
        output_folder,
        idea,
        selected_stories,
        all_story_ideas
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

        rain_file = os.path.join(
            "assets",
            "ambience",
            "rain.mp3"
        )

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


# # Generate, review, and save every selected story

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
            narrator_profiles
        )

        prepared_story_idea = prepare_premise(
            client,
            idea,
            current_story_idea
        )

        if prepared_story_idea is not None:

            break

        print(
            f"\nPREMISE FAILED: "
            f"{current_story_idea['title']}"
        )

        replacement = get_replacement_story(
            client,
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
        narrator_profiles
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
            narrator_profiles
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
            idea,
            prepared_story_idea,
            narrator_profile
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

generate_all_story_audio(
    elevenlabs,
    output_folder,
    len(selected_stories)
)