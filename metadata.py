import os
import json
from config import DEFAULT_TEXT_MODEL
from cost_tracking import record_openai_response_usage
from retry import run_with_retry



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

def save_youtube_metadata(
    project_folder,
    metadata
):

    metadata_file = os.path.join(
        project_folder,
        "youtube_metadata.json"
    )

    with open(
        metadata_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            metadata,
            f,
            indent=4,
            ensure_ascii=False
        )

    print(
        f"YOUTUBE METADATA SAVED: {metadata_file}"
    )
    
def generate_youtube_metadata(
    client,
    project_folder,
    video_idea,
    stories
):

    story_titles = []
    story_count = len(stories)
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
Create YouTube metadata for an original fictional horror story compilation.

ACTUAL COMPLETED STORY COUNT:
{story_count}

IMPORTANT:
Use this completed story count in the title and description.
If the original video idea mentions a different number,
ignore that number.

VIDEO IDEA:
{video_idea}

STORIES:
{stories_text}

Return ONLY valid JSON in this exact format:

{{
    "title": "YouTube title here",
    "description": "YouTube description here"
}}

TITLE RULES:
- Maximum 100 characters
- Make it clickable but not ridiculous clickbait
- Horror/scary-story niche
- Natural human wording
- Do not say Reddit because these stories are original fiction
- Prefer a strong searchable phrase like Scary Stories, Horror Stories, Late Night Stories, etc.

DESCRIPTION RULES:
- 2-4 short paragraphs
- Explain what the viewer is getting
- Mention that the stories are original fictional horror stories
- Keep it natural
- Do not reveal endings
"""

    def create_response():

        return client.responses.create(
            model=DEFAULT_TEXT_MODEL,
            input=prompt
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
        "youtube_metadata_generation"
    )

    metadata = json.loads(
        response.output_text
    )

    return metadata    
    
    
    
    
    
    
    
    
    
    