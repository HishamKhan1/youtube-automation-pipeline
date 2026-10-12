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
import json
from dotenv import load_dotenv
from openai import OpenAI
from elevenlabs.client import ElevenLabs
import subprocess
import re
from difflib import SequenceMatcher
import base64
from PIL import Image, ImageDraw, ImageFont


from thumbnail import (
    save_thumbnail_plan,
    generate_thumbnail_plan,
    generate_thumbnail_image,
    create_final_thumbnail
)
from metadata import (
    save_youtube_metadata,
    generate_youtube_metadata
)
from audio import (
    split_story_for_tts,
    generate_story_audio,
    generate_all_story_audio
)
from subtitles import (
    normalize_subtitle_word,
    get_story_words,
    get_whisper_words,
    align_story_words,
    assign_story_timestamps,
    create_subtitle_blocks,
    format_srt_timestamp,
    build_srt_from_blocks,
    get_word_timestamps,
    generate_word_timed_subtitles,
    generate_all_story_subtitles,
    create_subtitled_video,
    generate_all_subtitled_videos,
    create_subtitle_preview
)
from video import (
    create_story_video,
    generate_all_story_videos,
    create_concat_file,
    combine_story_videos,
    get_subtitled_story_files,
    get_video_files_with_transitions,
    create_story_transition,
    generate_all_story_transitions,
    add_background_ambience
)
from story_generation import (
    generate_idea,
    generate_story_ideas,
    select_best_stories,
    revise_premise,
    evaluate_premise,
    prepare_premise,
    get_replacement_story,
    generate_narrator_profile,
    generate_full_story,
    evaluate_story,
    revise_story,
    prepare_story
)
from project import (
    save_video_info,
    load_video_info,
    get_completed_stories,
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


#### These Functions Create and revise our video scripts >






def review_story(video_idea, story_idea, story, previous_stories):

    previous_context = ""

    if previous_stories:
        previous_context = """
        PREVIOUS STORIES IN THIS VIDEO:

        The following stories have already been completed.
        Use them ONLY to identify repetition in structure, openings,
        endings, scares, settings, and writing patterns.

        Do not copy details from them.

        """

        for previous_story in previous_stories:
            previous_context += f"""
            ---
            {previous_story[:1500]}
            """

    else:
        previous_context = """
        This is the first story in the compilation.
        There are no previous stories to compare against.
        """

    prompt = f"""
    You are the final editor for a YouTube horror narration channel.

    VIDEO:
    {video_idea["title"]}

    ORIGINAL PREMISE:
    {story_idea["premise"]}

    CURRENT STORY:
    {story}

    {previous_context}

    Edit the CURRENT STORY into the strongest possible final version
    for spoken YouTube narration.

    CORE GOALS:
    - sound natural when spoken aloud
    - sound like a normal person telling a disturbing experience
    - preserve the core premise
    - maintain strong pacing
    - maintain realism when appropriate
    - remove obvious AI-writing patterns
    - make this story feel different from previous stories

    CHECK FOR REPETITION:

    Compare the current story with the previous stories.

    Look for repeated:
    - opening styles
    - sentence patterns
    - story structures
    - settings
    - clues
    - types of threats
    - police involvement
    - character behavior
    - climax structure
    - ending structure
    - final sentences

    If the current story feels structurally too similar to a previous
    story, revise it while preserving the original premise.

    OPENINGS:

    Avoid repeatedly beginning stories with:
    - "The first time..."
    - "The first night..."
    - "At first..."
    - "It started..."
    - narrator immediately explaining that they dismissed a strange noise

    If the opening resembles previous stories, rewrite it.

    NATURAL WRITING:

    Remove:
    - dialogue that sounds scripted
    - overly poetic language
    - philosophical reflections
    - excessive dramatic sentence fragments
    - horror clichés
    - unnecessary exposition
    - repetitive descriptions of fear
    - overly convenient clues
    - unnecessary characters
    - unrealistic character decisions

    Do not make the writing more literary.

    CLUES:

    Do not automatically use:
    - hidden photographs
    - notebooks
    - children's shoes
    - drawings
    - fingerprints
    - mattresses
    - secret rooms
    - crawlspaces
    - someone secretly living inside a building

    Only preserve these if they are genuinely important to the
    original premise.

    POLICE:

    Police should only appear if their involvement naturally makes
    sense.

    Do not automatically make police arrival the resolution or climax.

    ENDINGS:

    Check whether the ending resembles previous stories.

    Avoid repeatedly ending with:
    - "I still don't know..."
    - "I never found out..."
    - "All I know is..."
    - "To this day..."
    - the narrator still hearing the sound
    - the narrator still dreaming about the event
    - the same threat mysteriously returning
    - an unnecessary supernatural final twist
    - the narrator moving away and then experiencing one final scare

    A story is allowed to simply end once its central event has
    reached a satisfying conclusion.

    Do not add a twist solely because this is horror.
        Do not explain the meaning, theme, or lesson of the story
    to the audience.

    Avoid ending with several paragraphs of reflection.

    After the central event is resolved or reaches its final
    unexplained point, end the story relatively quickly.

    The narrator does not need to explain why the experience
    was scary. Let the events speak for themselves.

    Avoid philosophical closing statements or sentences that
    sound written specifically to create a dramatic final line.

    Prefer a simple, natural ending that sounds like where a
    real person would stop telling the story.
    
    PACING:

    Keep the strongest moment relatively late.

    Keep the aftermath concise.

    Do not continue escalating after the natural climax.

    LENGTH:

    Keep the final story approximately 800-1100 words.

    IMPORTANT:

    Previous stories are provided only as comparison material.

    Do NOT merge their plots, characters, locations, or details into
    the current story.

    Edit ONLY the current story.

    Return ONLY the final edited story.
    Do not explain your changes.
    """

    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt
    )

    return response.output_text





########  youtube data



#### These Functions Create and revise our video scripts <
#--------------------------------------------------------------

#### These Functions create the video 

def create_ffmpeg_test_video(audio_file, output_file):

    command = [
        "ffmpeg",
        "-y",

        "-f", "lavfi",
        "-i", "color=c=black:s=1920x1080:r=30",

        "-i", audio_file,

        "-t", "10",

        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",

        "-c:a", "aac",
        "-b:a", "192k",

        "-shortest",
        output_file
    ]

    subprocess.run(
        command,
        check=True
    )

    print(f"TEST VIDEO SAVED: {output_file}")

def split_story_into_visual_scenes(
    story_text,
    target_words=110
):

    sentences = re.split(
        r'(?<=[.!?])\s+',
        story_text.strip()
    )

    scenes = []
    current_scene = []
    current_word_count = 0

    for sentence in sentences:

        sentence_word_count = len(
            sentence.split()
        )

        if (
            current_scene
            and current_word_count + sentence_word_count > target_words
        ):

            scenes.append(
                " ".join(current_scene)
            )

            current_scene = []
            current_word_count = 0

        current_scene.append(sentence)

        current_word_count += sentence_word_count

    if current_scene:
        scenes.append(
            " ".join(current_scene)
        )

    return scenes

def generate_visual_plan(
    video_idea,
    story_idea,
    story_text,
    narrator_profile
):

    narration_scenes = split_story_into_visual_scenes(
        story_text
    )

    numbered_scenes = []

    for number, scene in enumerate(
        narration_scenes,
        start=1
    ):
        numbered_scenes.append({
            "scene_number": number,
            "narration": scene
        })

    prompt = f"""
    You are creating the visual plan for a YouTube horror story.

    VIDEO:
    {video_idea["title"]}

    STORY:
    {story_idea["title"]}

    NARRATOR PROFILE:
    {json.dumps(narrator_profile, indent=2)}

    NARRATION SCENES:
    {json.dumps(numbered_scenes, indent=2)}

    Create exactly ONE visual prompt for every narration scene.

    The visuals should feel cinematic, realistic, dark, atmospheric,
    and suitable for a horror-story YouTube video.

    IMPORTANT:

        STRICT STORY GROUNDING:

    - Every visual must be directly supported by the narration for that scene.
    - Do NOT invent actions, locations, vehicles, objects, injuries,
      characters, or events that are not present in the narration.
    - Do NOT move the narrator into a car, building, room, or other
      location unless that scene clearly places them there.
    - Do NOT change who owns an object or vehicle.
    - Do NOT imply that an item was lost, abandoned, stolen, or left behind
      unless the narration explicitly says so.
    - If a scene is reflective or does not contain a strong visual event,
      use a simple environment or character reaction that is already
      supported by the story.

    VISUAL VARIETY:

    - Do not create two nearly identical visuals for nearby scenes.
    - If two scenes cover the same event, use a different perspective,
      detail shot, object, environment, or reaction rather than repeating
      the same wide shot.
    - Avoid repeating the same phone-looking composition several times.
    - Keep recurring characters visually consistent.
    - Keep recurring locations consistent.
    - Match the visual to what is happening in that narration section.
    - Do not invent major events that are not in the story.
    - Prefer believable environments and people.
    - Avoid excessive gore.
    - Avoid supernatural imagery unless the story actually requires it.
    - Do not put readable text inside generated images.
    - Do not rely on phone screens containing exact readable messages.
    - If a phone is important, show the person reacting to the phone
      or show the device from an angle where exact text is not needed.
    - Avoid making every image a close-up face.
    - Vary camera angles and compositions.
    - Some scenes may focus on environments, objects, vehicles,
      buildings, weather, or other details instead of people.
    - Use 16:9 cinematic compositions.
    - Each prompt should describe only ONE clear image.

    Each visual prompt should clearly describe:

    - main subject
    - environment
    - important objects
    - time of day
    - lighting
    - camera framing
    - mood

    Return one result for every provided scene.
    """

    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "visual_plan",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "scenes": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "scene_number": {
                                        "type": "integer"
                                    },
                                    "visual_prompt": {
                                        "type": "string"
                                    }
                                },
                                "required": [
                                    "scene_number",
                                    "visual_prompt"
                                ],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["scenes"],
                    "additionalProperties": False
                }
            }
        }
    )

    visual_plan = json.loads(
        response.output_text
    )

    return visual_plan

def generate_subtitles(
    audio_file,
    story_file,
    subtitle_file
):

    if os.path.exists(subtitle_file):
        print(
            f"SUBTITLES ALREADY EXIST - SKIPPING: {subtitle_file}"
        )
        return

    print(
        f"\nGENERATING SUBTITLES: {audio_file}"
    )

    with open(
        story_file,
        "r",
        encoding="utf-8"
    ) as f:
        story_text = f.read()

    with open(audio_file, "rb") as audio:

        raw_srt = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio,
            response_format="srt",
            language="en"
        )

    subtitle_blocks = parse_srt(
        raw_srt
    )

    corrected_blocks = correct_subtitle_text(
        story_text,
        subtitle_blocks
    )

    final_srt = build_corrected_srt(
        subtitle_blocks,
        corrected_blocks
    )

    with open(
        subtitle_file,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(final_srt)

    print(
        f"SUBTITLES SAVED: {subtitle_file}"
    )

def parse_srt(srt_text):

    blocks = []

    raw_blocks = srt_text.strip().split("\n\n")

    for raw_block in raw_blocks:

        lines = raw_block.strip().splitlines()

        if len(lines) < 3:
            continue

        number = int(lines[0])

        timestamps = lines[1]

        text = " ".join(lines[2:])

        blocks.append({
            "number": number,
            "timestamps": timestamps,
            "text": text
        })

    return blocks

def correct_subtitle_text(
    story_text,
    subtitle_blocks
):

    clean_story = story_text.replace("**", "")
    clean_story = clean_story.replace("__", "")
    clean_story = clean_story.replace("`", "")

    whisper_blocks = [
        {
            "number": block["number"],
            "text": block["text"]
        }
        for block in subtitle_blocks
    ]

    prompt = f"""
    You are correcting subtitles for a narrated YouTube story.

    ORIGINAL STORY:
    {clean_story}

    WHISPER SUBTITLE BLOCKS:
    {json.dumps(whisper_blocks, indent=2)}

    The original story is the SOURCE OF TRUTH.

    Whisper was used only to estimate timing and may contain:
    - spelling errors
    - punctuation errors
    - incorrect names
    - incorrect speaker attribution
    - missing words
    - slightly changed wording

    Correct the subtitle text using the original story.

    IMPORTANT:

    - Return exactly the same number of subtitle blocks.
    - Keep every block number unchanged.
    - Preserve the original story's wording as closely as possible.
    - Preserve the original order of the narration.
    - Do not summarize.
    - Do not paraphrase.
    - Do not invent words.
    - Use the Whisper text only to determine approximately
      which original words belong in each subtitle block.
    - Do not include timestamps.
    """

    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "corrected_subtitles",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "blocks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "number": {
                                        "type": "integer"
                                    },
                                    "text": {
                                        "type": "string"
                                    }
                                },
                                "required": [
                                    "number",
                                    "text"
                                ],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": ["blocks"],
                    "additionalProperties": False
                }
            }
        }
    )

    result = json.loads(
        response.output_text
    )

    return result["blocks"]

def build_corrected_srt(
    original_blocks,
    corrected_blocks
):

    corrected_by_number = {
        block["number"]: block["text"]
        for block in corrected_blocks
    }

    srt_parts = []

    for block in original_blocks:

        number = block["number"]

        corrected_text = corrected_by_number.get(
            number,
            block["text"]
        )

        srt_parts.append(
            f"{number}\n"
            f"{block['timestamps']}\n"
            f"{corrected_text}"
        )

    return "\n\n".join(srt_parts)


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