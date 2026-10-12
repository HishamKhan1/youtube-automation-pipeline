import os
import json
from config import DEFAULT_TEXT_MODEL


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
    video_idea,
    selected_stories
):

    story_titles = []
    story_count = len(selected_stories)
    for story in selected_stories:

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

    response = client.responses.create(
        model=DEFAULT_TEXT_MODEL,
        input=prompt
    )

    metadata = json.loads(
        response.output_text
    )

    return metadata    
    
    
    
    
    
    
    
    
    
    