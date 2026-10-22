import os
import subprocess
import tempfile
from config import RAIN_VOLUME
from visuals import load_visual_plan


def get_media_duration(
    file_path
):

    command = [
        "ffprobe",
        "-v", "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        file_path
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True
    )

    duration = float(
        result.stdout.strip()
    )

    if duration <= 0:
        raise RuntimeError(
            f"Invalid media duration: "
            f"{file_path}"
        )

    return duration

def create_scene_clip(
    image_file,
    duration,
    output_file,
    motion="static"
):

    motion_filter = get_scene_motion_filter(
        motion,
        duration
    )
    command = [
        "ffmpeg",
        "-y",

        "-loop", "1",
        "-i", image_file,

        "-t", str(duration),

        "-vf",
        motion_filter,

        "-r", "30",

        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",

        "-an",

        output_file
    ]

    subprocess.run(
        command,
        check=True
    )

    print(
        f"SCENE CLIP SAVED: "
        f"{output_file}"
    )

def attach_narration_audio(
    video_file,
    audio_file,
    output_file
):

    command = [
        "ffmpeg",
        "-y",

        "-i", video_file,
        "-i", audio_file,

        "-map", "0:v:0",
        "-map", "1:a:0",

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
        f"NARRATION ATTACHED: "
        f"{output_file}"
    )

def create_visual_story_video(
    project_folder,
    story_number,
    audio_file,
    visual_plan,
    output_file
):

    scenes = visual_plan[
        "scenes"
    ]

    if not scenes:
        raise RuntimeError(
            f"No visual scenes found for "
            f"story {story_number}."
        )

    scene_durations = calculate_scene_durations(
        audio_file,
        visual_plan
    )

    output_folder = os.path.dirname(
        output_file
    )

    os.makedirs(
        output_folder,
        exist_ok=True
    )

    with tempfile.TemporaryDirectory(
        dir=output_folder
    ) as temp_folder:

        scene_clips = []

        for scene, duration in zip(
            scenes,
            scene_durations
        ):

            scene_number = scene[
                "scene_number"
            ]

            image_file = os.path.join(
                project_folder,
                "visuals",
                f"story_{story_number:02d}",
                f"scene_{scene_number:03d}.png"
            )

            if not os.path.exists(
                image_file
            ):
                raise FileNotFoundError(
                    f"Scene image missing: "
                    f"{image_file}"
                )

            clip_file = os.path.join(
                temp_folder,
                f"scene_{scene_number:03d}.mp4"
            )

            create_scene_clip(
                image_file,
                duration,
                clip_file,
                motion=scene.get(
                    "motion",
                    "static"
                )
            )

            scene_clips.append(
                clip_file
            )

        concat_file = os.path.join(
            temp_folder,
            "scene_concat.txt"
        )

        silent_video = os.path.join(
            temp_folder,
            "silent_story.mp4"
        )

        combine_story_videos(
            scene_clips,
            silent_video,
            concat_file
        )

        attach_narration_audio(
            silent_video,
            audio_file,
            output_file
        )

    print(
        f"VISUAL STORY VIDEO SAVED: "
        f"{output_file}"
    )

def get_scene_motion_filter(
    motion,
    duration
):

    base_filter = (
        "scale=1920:1080:"
        "force_original_aspect_ratio=increase,"
        "crop=1920:1080"
    )
    frame_count = max(
        duration * 30,
        1
    )
    zoom_step = (
        0.08 / frame_count
    )

    if motion == "slow_zoom_in":
        return (
            base_filter
            + ",zoompan="
            f"z='min(zoom+{zoom_step},1.08)':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            f"d={int(frame_count)}:"
            "s=1920x1080:fps=30"
        )

    if motion == "slow_zoom_out":
        return (
            base_filter
            + ",zoompan="
            f"z='max(1.08-{zoom_step}*on,1.0)':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            f"d={int(frame_count)}:"
            "s=1920x1080:fps=30"
        )

    if motion == "pan_left":
        return (
            "scale=2100:1080:"
            "force_original_aspect_ratio=increase,"
            "crop=1920:1080:"
            f"x='(iw-ow)*(1-min(t/{duration},1))':"
            "y='(ih-oh)/2'"
        )

    if motion == "pan_right":
        return (
            "scale=2100:1080:"
            "force_original_aspect_ratio=increase,"
            "crop=1920:1080:"
            f"x='(iw-ow)*min(t/{duration},1)':"
            "y='(ih-oh)/2'"
        )

    return base_filter

def calculate_scene_durations(
    audio_file,
    visual_plan
):

    total_duration = get_media_duration(
        audio_file
    )

    scenes = visual_plan[
        "scenes"
    ]

    word_counts = []

    for scene in scenes:

        narration = scene.get(
            "narration",
            ""
        )

        word_count = len(
            narration.split()
        )

        word_counts.append(
            max(
                word_count,
                1
            )
        )

    total_words = sum(
        word_counts
    )

    durations = []

    for word_count in word_counts:

        scene_duration = (
            total_duration
            * word_count
            / total_words
        )

        durations.append(
            scene_duration
        )

    return durations

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

def all_story_videos_are_valid(
    project_folder,
    story_count
):

    found_audio = False

    for number in range(
        1,
        story_count + 1
    ):

        audio_file = os.path.join(
            project_folder,
            "audio",
            f"story_{number:02d}.mp3"
        )

        if not os.path.exists(
            audio_file
        ):
            continue

        found_audio = True

        video_file = os.path.join(
            project_folder,
            "videos",
            f"story_{number:02d}_video.mp4"
        )

        if not os.path.exists(
            video_file
        ):
            return False

        if os.path.getsize(
            video_file
        ) < 1000:
            return False

    return found_audio

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

def generate_all_visual_story_videos(
    project_folder,
    story_count
):

    video_folder = os.path.join(
        project_folder,
        "videos"
    )

    os.makedirs(
        video_folder,
        exist_ok=True
    )

    for number in range(
        1,
        story_count + 1
    ):

        audio_file = os.path.join(
            project_folder,
            "audio",
            f"story_{number:02d}.mp3"
        )

        if not os.path.exists(
            audio_file
        ):
            print(
                f"STORY {number} HAS NO AUDIO "
                f"- SKIPPING VIDEO"
            )
            continue

        visual_plan = load_visual_plan(
            project_folder,
            number
        )

        if visual_plan is None:
            raise RuntimeError(
                f"Visual plan missing for "
                f"story {number}."
            )

        output_file = os.path.join(
            video_folder,
            f"story_{number:02d}_video.mp4"
        )

        if (
            os.path.exists(output_file)
            and os.path.getsize(output_file) > 1000
        ):
            print(
                f"VIDEO ALREADY EXISTS "
                f"- SKIPPING: {output_file}"
            )
            continue

        create_visual_story_video(
            project_folder,
            number,
            audio_file,
            visual_plan,
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

def all_story_transitions_are_valid(
    project_folder,
    selected_stories
):

    completed_number = 0
    found_story = False

    for source_number, story in enumerate(
        selected_stories,
        start=1
    ):

        story_video = os.path.join(
            project_folder,
            "subtitled_videos",
            f"story_{source_number:02d}_subtitled.mp4"
        )

        if not os.path.exists(
            story_video
        ):
            continue

        found_story = True
        completed_number += 1

        if completed_number == 1:
            continue

        transition_file = os.path.join(
            project_folder,
            "transitions",
            f"story_{source_number:02d}_transition.mp4"
        )

        if not os.path.exists(
            transition_file
        ):
            return False

        if os.path.getsize(
            transition_file
        ) < 1000:
            return False

    return found_story

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

    completed_number = 0

    for source_number, story in enumerate(
        selected_stories,
        start=1
    ):

        story_video = os.path.join(
            project_folder,
            "subtitled_videos",
            f"story_{source_number:02d}_subtitled.mp4"
        )

        if not os.path.exists(story_video):
            print(
                f"STORY {source_number} HAS NO VIDEO "
                f"- SKIPPING TRANSITION"
            )
            continue

        completed_number += 1

        # First completed story does not need a transition
        if completed_number == 1:
            continue

        transition_file = os.path.join(
            transition_folder,
            f"story_{source_number:02d}_transition.mp4"
        )

        create_story_transition(
            completed_number,
            story["title"],
            transition_file
        )

def escape_drawtext_text(text):

    text = text.replace("\\", "\\\\")
    text = text.replace(":", r"\:")
    text = text.replace("'", r"\'")
    text = text.replace(",", r"\,")
    text = text.replace(";", r"\;")

    return text

def add_background_ambience(
    video_file,
    music_file,
    output_file
):

    video_duration = get_media_duration(
        video_file
    )

    fade_out_start = max(
        0,
        video_duration - 2
    )
    
    command = [
        "ffmpeg",
        "-y",

        "-i", video_file,

        "-stream_loop", "-1",
        "-i", music_file,

        "-filter_complex",
        (
            f"[1:a]"
            "highpass=f=120,"
            "lowpass=f=9000,"
            f"volume={RAIN_VOLUME},"
            "afade=t=in:st=0:d=2,"
            f"afade=t=out:st={fade_out_start:.3f}:d=2"
            "[ambience];"
            "[0:a][ambience]amix="
            "inputs=2:"
            "duration=first:"
            "dropout_transition=2:"
            "normalize=0,"
            "alimiter=limit=0.95[audio]"
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

















