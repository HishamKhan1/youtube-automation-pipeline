import os
import json
import re
import base64
from config import (
    DEFAULT_TEXT_MODEL,
    IMAGE_MODEL
)
from retry import run_with_retry
from cost_tracking import (
    record_openai_response_usage,
    record_openai_image_usage
)

def save_visual_plan(
    project_folder,
    story_number,
    visual_plan
):

    visual_plan_folder = os.path.join(
        project_folder,
        "visual_plans"
    )

    os.makedirs(
        visual_plan_folder,
        exist_ok=True
    )

    file_path = os.path.join(
        visual_plan_folder,
        f"story_{story_number:02d}_visual_plan.json"
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            visual_plan,
            file,
            indent=2
        )

    return file_path

def load_visual_plan(
    project_folder,
    story_number
):

    file_path = os.path.join(
        project_folder,
        "visual_plans",
        f"story_{story_number:02d}_visual_plan.json"
    )

    if not os.path.exists(
        file_path
    ):
        return None

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(
            file
        )

def should_retry_openai_error(
    error
):

    status_code = getattr(
        error,
        "status_code",
        None
    )

    retryable_status_codes = {
        408,
        409,
        429,
        500,
        502,
        503,
        504
    }

    if status_code in retryable_status_codes:
        return True

    error_name = type(error).__name__

    if error_name in {
        "APIConnectionError",
        "APITimeoutError",
        "RateLimitError"
    }:
        return True

    return False

def is_visual_moderation_error(
    error
):

    status_code = getattr(
        error,
        "status_code",
        None
    )

    error_text = str(
        error
    ).lower()

    return (
        status_code == 400
        and (
            "moderation_blocked" in error_text
            or "safety system" in error_text
        )
    )

def split_story_into_visual_scenes(
    story_text,
    target_words=35
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

def validate_visual_plan(
    visual_plan,
    expected_scene_count
):

    if not isinstance(
        visual_plan,
        dict
    ):
        raise ValueError(
            "Visual plan must be an object."
        )

    scenes = visual_plan.get(
        "scenes"
    )

    if not isinstance(
        scenes,
        list
    ):
        raise ValueError(
            "Visual plan 'scenes' must be a list."
        )

    if len(scenes) != expected_scene_count:
        raise ValueError(
            f"Visual plan returned "
            f"{len(scenes)} scenes, "
            f"expected {expected_scene_count}."
        )

    expected_numbers = list(
        range(
            1,
            expected_scene_count + 1
        )
    )

    actual_numbers = [
        scene.get(
            "scene_number"
        )
        for scene in scenes
    ]

    if actual_numbers != expected_numbers:
        raise ValueError(
            "Visual plan scene numbers "
            "are missing, duplicated, or out of order."
        )

    for scene in scenes:

        visual_prompt = scene.get(
            "visual_prompt"
        )

        if (
            not isinstance(
                visual_prompt,
                str
            )
            or not visual_prompt.strip()
        ):
            raise ValueError(
                "Visual prompt cannot be empty."
            )

        allowed_motions = {
            "slow_zoom_in",
            "slow_zoom_out",
            "pan_left",
            "pan_right",
            "static"
        }

        motion = scene.get(
            "motion"
        )

        if motion not in allowed_motions:
            raise ValueError(
                f"Invalid visual motion: "
                f"{motion}"
            )

    return True

def generate_visual_plan(
    client,
    project_folder,
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

    For each scene, also choose ONE motion style:

    - slow_zoom_in:
    use for tension, fear, discoveries, or important details

    - slow_zoom_out:
    use for isolation, aftermath, or revealing the environment

    - pan_left:
    use when exploring an environment or following visual detail

    - pan_right:
    use when exploring an environment or following visual detail

    - static:
    use when movement would distract from the scene

    Do not use the same motion for every scene.
    Vary motion naturally throughout the story.

    Return one result for every provided scene.
    """

    def create_response():

        return client.responses.create(
            model=DEFAULT_TEXT_MODEL,
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
                                        },
                                        "motion": {
                                            "type": "string",
                                            "enum": [
                                                "slow_zoom_in",
                                                "slow_zoom_out",
                                                "pan_left",
                                                "pan_right",
                                                "static"
                                            ]
                                        }
                                    },
                                    "required": [
                                        "scene_number",
                                        "visual_prompt",
                                        "motion"
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


    response = run_with_retry(
        create_response,
        attempts=3,
        delay_seconds=2,
        should_retry=should_retry_openai_error
    )

    record_openai_response_usage(
        project_folder,
        response,
        "visual_plan_generation"
    )

    visual_plan = json.loads(
        response.output_text
    )

    validate_visual_plan(
        visual_plan,
        len(numbered_scenes)
    )

    for scene, narration_scene in zip(
        visual_plan["scenes"],
        numbered_scenes
    ):
        scene["narration"] = narration_scene[
            "narration"
        ]

    return visual_plan

def prepare_visual_plan(
    client,
    project_folder,
    story_number,
    video_idea,
    story_idea,
    story_text,
    narrator_profile
):

    expected_scene_count = len(
        split_story_into_visual_scenes(
            story_text
        )
    )

    existing_plan = load_visual_plan(
        project_folder,
        story_number
    )

    if existing_plan is not None:

        try:

            validate_visual_plan(
                existing_plan,
                expected_scene_count
            )

            print(
                f"VISUAL PLAN {story_number} "
                f"ALREADY EXISTS - USING SAVED VERSION"
            )

            return existing_plan

        except ValueError:

            print(
                f"VISUAL PLAN {story_number} "
                f"IS INVALID - REGENERATING"
            )

    visual_plan = generate_visual_plan(
        client,
        project_folder,
        video_idea,
        story_idea,
        story_text,
        narrator_profile
    )

    save_visual_plan(
        project_folder,
        story_number,
        visual_plan
    )

    return visual_plan

def generate_all_visual_plans(
    client,
    project_folder,
    video_idea,
    selected_stories,
    narrator_profiles
):

    visual_plans = {}

    for story_number, story_idea in enumerate(
        selected_stories,
        start=1
    ):

        story_file = os.path.join(
            project_folder,
            f"story_{story_number:02d}.txt"
        )

        if not os.path.exists(
            story_file
        ):
            print(
                f"STORY {story_number} HAS NO FINAL STORY "
                f"- SKIPPING VISUAL PLAN"
            )
            continue

        with open(
            story_file,
            "r",
            encoding="utf-8"
        ) as file:
            story_text = file.read()

        narrator_profile = narrator_profiles.get(
            str(story_number),
            {}
        )

        visual_plan = prepare_visual_plan(
            client,
            project_folder,
            story_number,
            video_idea,
            story_idea,
            story_text,
            narrator_profile
        )

        visual_plans[
            story_number
        ] = visual_plan

    return visual_plans

def all_visual_plans_are_valid(
    project_folder,
    selected_stories
):

    found_story = False

    for story_number, story_idea in enumerate(
        selected_stories,
        start=1
    ):

        story_file = os.path.join(
            project_folder,
            f"story_{story_number:02d}.txt"
        )

        if not os.path.exists(
            story_file
        ):
            continue

        found_story = True

        with open(
            story_file,
            "r",
            encoding="utf-8"
        ) as file:
            story_text = file.read()

        expected_scene_count = len(
            split_story_into_visual_scenes(
                story_text
            )
        )

        visual_plan = load_visual_plan(
            project_folder,
            story_number
        )

        if visual_plan is None:
            return False

        try:

            validate_visual_plan(
                visual_plan,
                expected_scene_count
            )

        except ValueError:
            return False

    return found_story

def scene_image_is_valid(
    image_file
):

    if not os.path.exists(
        image_file
    ):
        return False

    if os.path.getsize(
        image_file
    ) < 1000:
        return False

    try:
        with open(
            image_file,
            "rb"
        ) as file:

            png_signature = file.read(
                8
            )

        return (
            png_signature
            == b"\x89PNG\r\n\x1a\n"
        )

    except OSError:
        return False

def generate_scene_image(
    client,
    project_folder,
    story_number,
    scene
):

    scene_number = scene[
        "scene_number"
    ]

    visual_prompt = scene[
        "visual_prompt"
    ]

    visual_folder = os.path.join(
        project_folder,
        "visuals",
        f"story_{story_number:02d}"
    )

    os.makedirs(
        visual_folder,
        exist_ok=True
    )

    output_file = os.path.join(
        visual_folder,
        f"scene_{scene_number:03d}.png"
    )

    if scene_image_is_valid(
        output_file
    ):
        print(
            f"SCENE IMAGE ALREADY EXISTS - SKIPPING: "
            f"{output_file}"
        )
        return output_file

    primary_prompt = f"""
Create a realistic cinematic image for a mature
YouTube horror narration.

SCENE:
{visual_prompt}

Style requirements:

- realistic photography
- cinematic 16:9 composition
- dark atmospheric lighting
- believable people and locations
- mature psychological horror tone
- natural shadows
- subtle suspense
- no readable text
- no captions
- no logos
- no watermarks
- no graphic gore
"""

    fallback_prompt = f"""
Create a realistic cinematic suspense image.

Use this scene only as general visual inspiration:

{visual_prompt}

Keep the result subtle and safe.

Focus on:
- environment
- lighting
- atmosphere
- objects
- architecture
- weather
- distant or non-threatening people

No violence.
No injuries.
No gore.
No weapons.
No readable text.
No logos.
No watermarks.
Cinematic 16:9 photography.
"""

    try:

        result = run_with_retry(
            client.images.generate,
            model=IMAGE_MODEL,
            prompt=primary_prompt,
            size="1536x864",
            quality="medium",
            output_format="png",
            attempts=3,
            delay_seconds=2,
            should_retry=should_retry_openai_error
        )

    except Exception as error:

        if not is_visual_moderation_error(
            error
        ):
            raise

        print(
            f"\nSCENE {scene_number} PROMPT "
            f"BLOCKED BY MODERATION"
        )

        print(
            "TRYING SAFE FALLBACK PROMPT..."
        )

        result = run_with_retry(
            client.images.generate,
            model=IMAGE_MODEL,
            prompt=fallback_prompt,
            size="1536x864",
            quality="medium",
            output_format="png",
            attempts=3,
            delay_seconds=2,
            should_retry=should_retry_openai_error
        )

    record_openai_image_usage(
        project_folder,
        result,
        "visual_scene_image",
        IMAGE_MODEL
    )

    image_data = base64.b64decode(
        result.data[0].b64_json
    )

    save_scene_image_atomic(
        output_file,
        image_data
    )

    print(
        f"SCENE IMAGE SAVED: "
        f"{output_file}"
    )

    return output_file

def generate_all_scene_images(
    client,
    project_folder,
    selected_stories
):

    generated_images = {}

    for story_number, story_idea in enumerate(
        selected_stories,
        start=1
    ):

        story_file = os.path.join(
            project_folder,
            f"story_{story_number:02d}.txt"
        )

        if not os.path.exists(
            story_file
        ):
            print(
                f"STORY {story_number} HAS NO FINAL STORY "
                f"- SKIPPING SCENE IMAGES"
            )
            continue

        visual_plan = load_visual_plan(
            project_folder,
            story_number
        )

        if visual_plan is None:
            raise RuntimeError(
                f"Visual plan missing for "
                f"story {story_number}."
            )

        story_images = []

        for scene in visual_plan[
            "scenes"
        ]:

            image_file = generate_scene_image(
                client,
                project_folder,
                story_number,
                scene
            )

            story_images.append(
                image_file
            )

        generated_images[
            story_number
        ] = story_images

    return generated_images

def all_scene_images_are_valid(
    project_folder,
    selected_stories
):

    found_story = False

    for story_number, story_idea in enumerate(
        selected_stories,
        start=1
    ):

        story_file = os.path.join(
            project_folder,
            f"story_{story_number:02d}.txt"
        )

        if not os.path.exists(
            story_file
        ):
            continue

        found_story = True

        visual_plan = load_visual_plan(
            project_folder,
            story_number
        )

        if visual_plan is None:
            return False

        for scene in visual_plan[
            "scenes"
        ]:

            scene_number = scene[
                "scene_number"
            ]

            image_file = os.path.join(
                project_folder,
                "visuals",
                f"story_{story_number:02d}",
                f"scene_{scene_number:03d}.png"
            )

            if not scene_image_is_valid(
                image_file
            ):
                return False

    return found_story

def save_scene_image_atomic(
    image_file,
    image_bytes
):

    temp_file = (
        image_file + ".tmp"
    )

    try:

        with open(
            temp_file,
            "wb"
        ) as file:

            file.write(
                image_bytes
            )

        if not scene_image_is_valid(
            temp_file
        ):
            raise RuntimeError(
                f"Generated scene image "
                f"is invalid: {image_file}"
            )

        os.replace(
            temp_file,
            image_file
        )

    finally:

        if os.path.exists(
            temp_file
        ):
            os.remove(
                temp_file
            )
