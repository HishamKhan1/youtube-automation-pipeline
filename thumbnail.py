import os
import json
import base64
from config import DEFAULT_TEXT_MODEL, IMAGE_MODEL
from PIL import Image, ImageDraw, ImageFont
from retry import run_with_retry
from cost_tracking import (
    record_openai_image_usage,
    record_openai_response_usage
)

def should_retry_thumbnail_error(error):

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

def is_thumbnail_moderation_error(error):

    status_code = getattr(
        error,
        "status_code",
        None
    )

    error_text = str(error).lower()

    return (
        status_code == 400
        and (
            "moderation_blocked" in error_text
            or "safety system" in error_text
        )
    )

def save_thumbnail_plan(
    project_folder,
    thumbnail_plan
):

    thumbnail_plan_file = os.path.join(
        project_folder,
        "thumbnail_plan.json"
    )

    with open(
        thumbnail_plan_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            thumbnail_plan,
            f,
            indent=4,
            ensure_ascii=False
        )

    print(
        f"THUMBNAIL PLAN SAVED: {thumbnail_plan_file}"
    )
    
def generate_thumbnail_plan(
    client,
    project_folder,
    metadata,
    stories
):

    story_titles = []

    for story in stories:

        if isinstance(story, dict):
            story_titles.append(
                story.get("title", "")
            )

    stories_text = "\n".join(
        f"- {title}"
        for title in story_titles
        if title
    )

    prompt = f"""
Create a YouTube thumbnail concept for an original horror story compilation aimed at an older audience.

The thumbnail should feel tense, cinematic, mature, and highly clickable.
Aim for suspense, psychological horror, or realistic danger rather than cheesy horror.

YOUTUBE TITLE:
{metadata["title"]}

STORIES:
{stories_text}

Return ONLY valid JSON:

{{
    "overlay_text": "short thumbnail text",
    "image_prompt": "detailed image generation prompt"
}}

OVERLAY TEXT RULES:
- Maximum 4 words
- Very easy to read
- Do not just repeat the full YouTube title
- Make it intriguing
- Mature horror / suspense tone

IMAGE PROMPT RULES:
- 16:9 YouTube thumbnail composition
- Dark cinematic suspense / horror
- High contrast
- One strong focal subject
- Simple composition, not cluttered
- Theme should fit an adult horror audience
- The image can include confrontation, pursuit, being watched, or a tense face-to-face moment
- A phone, notification, or technology element can be included when relevant, but it does not need to be the main focus
- Strong visual tension is preferred over a literal representation of the story
- Use realistic locations such as apartments, hallways, parking lots, cars, streets, doorways, or houses at night
- Leave some empty space for overlay text
- No gore, blood, graphic injury, or extreme violence
- DO NOT include any words, letters, captions, logos, watermarks, or readable text in the generated image
"""

    response = client.responses.create(
        model=DEFAULT_TEXT_MODEL,
        input=prompt
    )

    record_openai_response_usage(
        project_folder,
        response,
        "thumbnail_plan_generation"
    )

    thumbnail_plan = json.loads(
        response.output_text
    )

    return thumbnail_plan    
    
def generate_thumbnail_image(
    client,
    project_folder,
    thumbnail_plan
):

    print("\nGENERATING THUMBNAIL IMAGE...")

    primary_prompt = thumbnail_plan["image_prompt"]

    fallback_prompt = """
        16:9 YouTube thumbnail composition for a mature cinematic horror and suspense channel.

        Create a dark, realistic, atmospheric scene with one strong focal point.

        Use a simple setting that could fit a wide range of unsettling stories, such as:
        - a dim hallway
        - an empty road at night
        - a shadowy doorway
        - a dark apartment interior
        - a rainy window
        - an isolated building

        The image should feel mysterious and tense without showing explicit danger.

        Use cinematic lighting, strong contrast, realistic photography, subtle shadows, and a serious suspenseful mood.

        Keep the composition clean and easy to understand at thumbnail size.

        Leave clear negative space on the left side for title text.

        No gore.
        No injuries.
        No weapons.
        No attacks.
        No graphic violence.
        No disturbing facial expressions.
        No supernatural creatures.
        No readable text.
        No letters.
        No captions.
        No logos.
        No watermarks.
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
            should_retry=should_retry_thumbnail_error
        )

    except Exception as e:

        if not is_thumbnail_moderation_error(e):
            raise

        print(
            "\nPRIMARY THUMBNAIL PROMPT "
            "BLOCKED BY MODERATION"
        )

        print(
            "\nTRYING FALLBACK SAFE PROMPT..."
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
            should_retry=should_retry_thumbnail_error
        )

    record_openai_image_usage(
        project_folder,
        result,
        "thumbnail_image",
        IMAGE_MODEL
    )
    
    image_data = base64.b64decode(
        result.data[0].b64_json
    )

    output_file = os.path.join(
        project_folder,
        "thumbnail_background.png"
    )

    with open(
        output_file,
        "wb"
    ) as f:
        f.write(image_data)

    print(
        f"THUMBNAIL IMAGE SAVED: {output_file}"
    )

    return output_file    
    
def create_final_thumbnail(
    project_folder,
    thumbnail_plan
):

    background_file = os.path.join(
        project_folder,
        "thumbnail_background.png"
    )

    output_file = os.path.join(
        project_folder,
        "thumbnail_final.png"
    )

    image = Image.open(
        background_file
    ).convert("RGBA")

    draw = ImageDraw.Draw(image)

    overlay_text = thumbnail_plan[
        "overlay_text"
    ].upper()

    # Force a stronger line break for this specific phrase
    words = overlay_text.split()

    if overlay_text == "DON'T ANSWER IT":

        line1 = "DON'T"
        line2 = "ANSWER IT"

    elif overlay_text == "DO NOT ANSWER":

        line1 = "DO NOT"
        line2 = "ANSWER"

    elif len(words) >= 3:

        split_point = (len(words) + 1) // 2

        line1 = " ".join(
            words[:split_point]
        )

        line2 = " ".join(
            words[split_point:]
        )

    else:

        line1 = overlay_text
        line2 = ""

    # Try stronger fonts first
    font = None

    font_paths = [
        "C:/Windows/Fonts/impact.ttf",
        "C:/Windows/Fonts/ariblk.ttf",
        "C:/Windows/Fonts/arialbd.ttf"
    ]

    for path in font_paths:
        try:
            font = ImageFont.truetype(
                path,
                170
            )
            break
        except:
            pass

    if font is None:
        font = ImageFont.load_default()

    x = 80
    y = 80
    line_spacing = 12

    text_block = line1
    if line2:
        text_block += "\n" + line2

    # Shadow
    shadow_offset = 6
    draw.multiline_text(
        (x + shadow_offset, y + shadow_offset),
        text_block,
        font=font,
        fill=(0, 0, 0, 180),
        spacing=line_spacing,
        stroke_width=0
    )

    # Draw main text with outline
    # First line red for more thumbnail punch
    draw.text(
        (x, y),
        line1,
        font=font,
        fill=(220, 30, 30, 255),
        stroke_width=8,
        stroke_fill=(0, 0, 0, 255)
    )

    if line2:
        bbox1 = draw.textbbox(
            (x, y),
            line1,
            font=font,
            stroke_width=8
        )

        line2_y = bbox1[3] + line_spacing

        draw.text(
            (x, line2_y),
            line2,
            font=font,
            fill=(255, 255, 255, 255),
            stroke_width=8,
            stroke_fill=(0, 0, 0, 255)
        )

    image.save(output_file)

    print(
        f"FINAL THUMBNAIL SAVED: {output_file}"
    )

    return output_file    
    

  
  
  
  
  
  
  
  
  
    