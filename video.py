import os
import subprocess
from config import RAIN_VOLUME

def create_story_video(
    background_file,
    audio_file,
    output_file
):

    command = [
        "ffmpeg",
        "-y",

        # Loop the background forever
        "-stream_loop", "-1",
        "-i", background_file,

        # Narration
        "-i", audio_file,

        # Use only background video + narration audio
        "-map", "0:v:0",
        "-map", "1:a:0",

        # Make every background fit YouTube 1080p
        "-vf",
        "scale=1920:1080:force_original_aspect_ratio=increase,"
        "crop=1920:1080",

        "-r", "30",

        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",

        "-c:a", "aac",
        "-b:a", "192k",

        # Stop when narration ends
        "-shortest",

        output_file
    ]

    subprocess.run(
        command,
        check=True
    )

    print(
        f"STORY VIDEO SAVED: {output_file}"
    )

def generate_all_story_videos(
    project_folder,
    story_count,
    background_file
):

    video_folder = os.path.join(
        project_folder,
        "videos"
    )

    os.makedirs(
        video_folder,
        exist_ok=True
    )

    for number in range(1, story_count + 1):

        audio_file = os.path.join(
            project_folder,
            "audio",
            f"story_{number:02d}.mp3"
        )

        output_file = os.path.join(
            video_folder,
            f"story_{number:02d}_video.mp4"
        )

        if not os.path.exists(audio_file):
            print(
                f"STORY {number} HAS NO AUDIO - SKIPPING VIDEO"
            )
            continue

        if os.path.exists(output_file):
            print(
                f"VIDEO ALREADY EXISTS - SKIPPING: {output_file}"
            )
            continue

        create_story_video(
            background_file,
            audio_file,
            output_file
        )

def create_concat_file(
    video_files,
    concat_file
):

    with open(
        concat_file,
        "w",
        encoding="utf-8"
    ) as f:

        for video_file in video_files:

            absolute_path = os.path.abspath(
                video_file
            )

            absolute_path = absolute_path.replace(
                "\\",
                "/"
            )

            f.write(
                f"file '{absolute_path}'\n"
            )

def combine_story_videos(
    video_files,
    output_file,
    concat_file
):

    create_concat_file(
        video_files,
        concat_file
    )

    command = [
        "ffmpeg",
        "-y",

        "-f", "concat",
        "-safe", "0",

        "-i", concat_file,

        "-c", "copy",

        output_file
    ]

    subprocess.run(
        command,
        check=True
    )

    print(
        f"FINAL VIDEO SAVED: {output_file}"
    )

def get_subtitled_story_files(
    project_folder,
    story_count
):

    video_files = []

    for number in range(
        1,
        story_count + 1
    ):

        video_file = os.path.join(
            project_folder,
            "subtitled_videos",
            f"story_{number:02d}_subtitled.mp4"
        )

        if os.path.exists(video_file):
            video_files.append(
                video_file
            )

    return video_files

def get_video_files_with_transitions(
    project_folder,
    story_count
):

    video_files = []

    for number in range(
        1,
        story_count + 1
    ):

        story_video = os.path.join(
            project_folder,
            "subtitled_videos",
            f"story_{number:02d}_subtitled.mp4"
        )

        if not os.path.exists(story_video):
            continue

        if number > 1:

            transition_file = os.path.join(
                project_folder,
                "transitions",
                f"story_{number:02d}_transition.mp4"
            )

            if os.path.exists(transition_file):
                video_files.append(
                    transition_file
                )

        video_files.append(
            story_video
        )

    return video_files

def create_story_transition(
    story_number,
    story_title,
    output_file,
    duration=3
):

    number_text = escape_drawtext_text(
        f"STORY {story_number}"
    )

    title_text = escape_drawtext_text(
        story_title.upper()
    )

    command = [
        "ffmpeg",
        "-y",

        "-f", "lavfi",
        "-i",
        f"color=c=black:s=1920x1080:r=30:d={duration}",

        "-f", "lavfi",
        "-i",
        f"anullsrc=r=44100:cl=mono:d={duration}",

        "-vf",
        (
            "drawtext="
            "fontfile='C\\:/Windows/Fonts/arial.ttf':"
            f"text='{number_text}':"
            "fontcolor=white:"
            "fontsize=38:"
            "x=(w-text_w)/2:"
            "y=(h/2)-90,"
            "drawtext="
            "fontfile='C\\:/Windows/Fonts/arial.ttf':"
            f"text='{title_text}':"
            "fontcolor=white:"
            "fontsize=56:"
            "x=(w-text_w)/2:"
            "y=(h/2)-10"
        ),

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

    print(
        f"TRANSITION SAVED: {output_file}"
    )

def generate_all_story_transitions(
    project_folder,
    selected_stories
):

    transition_folder = os.path.join(
        project_folder,
        "transitions"
    )

    os.makedirs(
        transition_folder,
        exist_ok=True
    )

    for number, story in enumerate(
        selected_stories,
        start=1
    ):

        if number == 1:
            continue

        story_video = os.path.join(
            project_folder,
            "subtitled_videos",
            f"story_{number:02d}_subtitled.mp4"
        )

        if not os.path.exists(story_video):
            print(
                f"STORY {number} HAS NO VIDEO "
                f"- SKIPPING TRANSITION"
            )
            continue

        transition_file = os.path.join(
            transition_folder,
            f"story_{number:02d}_transition.mp4"
        )

        if os.path.exists(transition_file):
            print(
                f"TRANSITION ALREADY EXISTS "
                f"- SKIPPING: {transition_file}"
            )
            continue

        create_story_transition(
            number,
            story["title"],
            transition_file
        )

def escape_drawtext_text(text):

    text = text.replace("\\", "\\\\")
    text = text.replace(":", r"\:")
    text = text.replace("'", r"\'")

    return text

def add_background_ambience(
    video_file,
    music_file,
    output_file
):

    command = [
        "ffmpeg",
        "-y",

        "-i", video_file,

        "-stream_loop", "-1",
        "-i", music_file,

        "-filter_complex",
        (
            f"[1:a]volume={RAIN_VOLUME}[ambience];"
            "[0:a][ambience]amix="
            "inputs=2:"
            "duration=first:"
            "dropout_transition=2[audio]"
        ),

        "-map", "0:v",
        "-map", "[audio]",

        "-c:v", "copy",

        "-c:a", "aac",
        "-b:a", "192k",

        "-shortest",

        output_file
    ]

    subprocess.run(
        command,
        check=True
    )

    print(
        f"VIDEO WITH AMBIENCE SAVED: {output_file}"
    )

















