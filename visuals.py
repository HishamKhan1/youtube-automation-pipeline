import json

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





