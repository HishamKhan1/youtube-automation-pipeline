import os
import re
import subprocess
from difflib import SequenceMatcher
from cost_tracking import record_openai_transcription_usage
from retry import run_with_retry


def normalize_subtitle_word(word):

    return re.sub(
        r"[^a-z0-9]",
        "",
        word.lower()
    )

def get_story_words(story_text):

    clean_story = story_text.replace("**", "")
    clean_story = clean_story.replace("__", "")
    clean_story = clean_story.replace("`", "")

    raw_words = re.findall(
        r"\S+",
        clean_story
    )

    story_words = []

    for word in raw_words:

        normalized = normalize_subtitle_word(
            word
        )

        if not normalized:
            continue

        story_words.append({
            "text": word,
            "normalized": normalized
        })

    return story_words

def get_whisper_words(timestamp_words):

    whisper_words = []

    for word in timestamp_words:

        normalized = normalize_subtitle_word(
            word.word
        )

        if not normalized:
            continue

        whisper_words.append({
            "text": word.word,
            "normalized": normalized,
            "start": word.start,
            "end": word.end
        })

    return whisper_words

def align_story_words(
    story_words,
    whisper_words
):

    story_normalized = [
        word["normalized"]
        for word in story_words
    ]

    whisper_normalized = [
        word["normalized"]
        for word in whisper_words
    ]

    matcher = SequenceMatcher(
        None,
        story_normalized,
        whisper_normalized,
        autojunk=False
    )

    matches = {}

    for block in matcher.get_matching_blocks():

        for offset in range(block.size):

            story_index = block.a + offset
            whisper_index = block.b + offset

            matches[story_index] = whisper_index

    return matches

def assign_story_timestamps(
    story_words,
    whisper_words,
    matches
):

    timed_words = []

    matched_story_indexes = sorted(
        matches.keys()
    )

    for story_index, story_word in enumerate(story_words):

        # Exact match found
        if story_index in matches:

            whisper_index = matches[story_index]

            timed_words.append({
                "text": story_word["text"],
                "start": float(
                    whisper_words[whisper_index]["start"]
                ),
                "end": float(
                    whisper_words[whisper_index]["end"]
                )
            })

            continue

        # Find closest matched word before this word
        previous_matches = [
            index
            for index in matched_story_indexes
            if index < story_index
        ]

        # Find closest matched word after this word
        next_matches = [
            index
            for index in matched_story_indexes
            if index > story_index
        ]

        previous_index = (
            previous_matches[-1]
            if previous_matches
            else None
        )

        next_index = (
            next_matches[0]
            if next_matches
            else None
        )

        # Unmatched word is between two known words
        if (
            previous_index is not None
            and next_index is not None
        ):

            previous_whisper = matches[
                previous_index
            ]

            next_whisper = matches[
                next_index
            ]

            gap_start = float(
                whisper_words[
                    previous_whisper
                ]["end"]
            )

            gap_end = float(
                whisper_words[
                    next_whisper
                ]["start"]
            )

            words_in_gap = (
                next_index
                - previous_index
                - 1
            )

            position = (
                story_index
                - previous_index
                - 1
            )

            duration = (
                gap_end - gap_start
            ) / words_in_gap

            start = (
                gap_start
                + duration * position
            )

            end = start + duration

        else:
            start = None
            end = None

        timed_words.append({
            "text": story_word["text"],
            "start": start,
            "end": end
        })

    return timed_words

def create_subtitle_blocks(
    timed_words,
    max_words=8,
    max_chars=45,
    max_duration=3.5,
    min_duration=1.2
):

    blocks = []
    current_words = []

    for word in timed_words:

        if (
            word["start"] is None
            or word["end"] is None
        ):
            continue

        current_words.append(word)

        text = " ".join(
            item["text"]
            for item in current_words
        )

        start = current_words[0]["start"]
        end = current_words[-1]["end"]

        duration = end - start

        ends_sentence = bool(
            re.search(
                r'[.!?]["\']?$',
                word["text"]
            )
        )

        should_finish = (
            duration >= max_duration
            or (
                duration >= min_duration
                and (
                    len(current_words) >= max_words
                    or len(text) >= max_chars
                    or (
                        ends_sentence
                        and len(current_words) >= 4
                    )
                )
            )
        )

        if should_finish:

            blocks.append({
                "start": start,
                "end": end,
                "text": text
            })

            current_words = []

    if current_words:

        blocks.append({
            "start": current_words[0]["start"],
            "end": current_words[-1]["end"],
            "text": " ".join(
                item["text"]
                for item in current_words
            )
        })

    return blocks

def format_srt_timestamp(seconds):

    milliseconds = int(
        round(seconds * 1000)
    )

    hours = milliseconds // 3600000
    milliseconds %= 3600000

    minutes = milliseconds // 60000
    milliseconds %= 60000

    secs = milliseconds // 1000
    milliseconds %= 1000

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{secs:02d},"
        f"{milliseconds:03d}"
    )

def build_srt_from_blocks(
    subtitle_blocks
):

    srt_parts = []

    for index, block in enumerate(
        subtitle_blocks,
        start=1
    ):

        start_time = format_srt_timestamp(
            block["start"]
        )

        end_time = format_srt_timestamp(
            block["end"]
        )

        srt_parts.append(
            f"{index}\n"
            f"{start_time} --> {end_time}\n"
            f"{block['text']}"
        )

    return "\n\n".join(srt_parts)

def get_word_timestamps(
    client,
    project_folder,
    audio_file
):

    print(
        f"\nGETTING WORD TIMESTAMPS: {audio_file}"
    )

    def transcribe_audio():

        with open(
            audio_file,
            "rb"
        ) as audio:

            return client.audio.transcriptions.create(
                model="whisper-1",
                file=audio,
                response_format="verbose_json",
                timestamp_granularities=["word"],
                language="en"
            )

    transcription = run_with_retry(
        transcribe_audio,
        attempts=3,
        delay_seconds=2,
        should_retry=should_retry_transcription_error
    )

    record_openai_transcription_usage(
        project_folder,
        transcription.duration,
        model="whisper-1"
    )

    return transcription.words

def generate_word_timed_subtitles(
    client,
    project_folder,
    story_file,
    audio_file,
    subtitle_file
):

    if os.path.exists(subtitle_file):
        print(
            f"SUBTITLES ALREADY EXIST - SKIPPING: {subtitle_file}"
        )
        return

    print(
        f"\nGENERATING WORD-TIMED SUBTITLES: {audio_file}"
    )

    with open(
        story_file,
        "r",
        encoding="utf-8"
    ) as f:
        story_text = f.read()

    timestamp_words = get_word_timestamps(
        client,
        project_folder,
        audio_file
    )

    story_words = get_story_words(
        story_text
    )

    whisper_words = get_whisper_words(
        timestamp_words
    )

    matches = align_story_words(
        story_words,
        whisper_words
    )

    match_rate = (
        len(matches)
        / len(story_words)
        * 100
    )

    print(
        f"SUBTITLE MATCH RATE: "
        f"{match_rate:.2f}%"
    )

    timed_words = assign_story_timestamps(
        story_words,
        whisper_words,
        matches
    )

    subtitle_blocks = create_subtitle_blocks(
        timed_words
    )

    final_srt = build_srt_from_blocks(
        subtitle_blocks
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

def generate_all_story_subtitles(
    client,
    project_folder,
    story_count
):

    subtitle_folder = os.path.join(
        project_folder,
        "subtitles"
    )

    os.makedirs(
        subtitle_folder,
        exist_ok=True
    )

    for number in range(
        1,
        story_count + 1
    ):

        story_file = os.path.join(
            project_folder,
            f"story_{number:02d}.txt"
        )

        audio_file = os.path.join(
            project_folder,
            "audio",
            f"story_{number:02d}.mp3"
        )

        subtitle_file = os.path.join(
            subtitle_folder,
            f"story_{number:02d}.srt"
        )

        if not os.path.exists(story_file):
            print(
                f"STORY {number} HAS NO FINAL TEXT "
                f"- SKIPPING SUBTITLES"
            )
            continue

        if not os.path.exists(audio_file):
            print(
                f"STORY {number} HAS NO AUDIO "
                f"- SKIPPING SUBTITLES"
            )
            continue

        generate_word_timed_subtitles(
            client,
            project_folder,
            story_file,
            audio_file,
            subtitle_file
        )

def create_subtitled_video(
    video_file,
    subtitle_file,
    output_file
):

    subtitle_path = os.path.abspath(
        subtitle_file
    )

    subtitle_path = subtitle_path.replace(
        "\\",
        "/"
    )

    subtitle_path = subtitle_path.replace(
        ":",
        "\\:"
    )

    command = [
        "ffmpeg",
        "-y",

        "-i", video_file,

        "-vf",
        (
            f"subtitles='{subtitle_path}':"
            "force_style='"
            "FontName=Arial,"
            "FontSize=22,"
            "Alignment=2,"
            "MarginV=55,"
            "Outline=2,"
            "Shadow=1"
            "'"
        ),

        "-c:v", "libx264",
        "-preset", "veryfast",
        "-c:a", "copy",

        output_file
    ]

    subprocess.run(
        command,
        check=True
    )

    print(
        f"SUBTITLED VIDEO SAVED: {output_file}"
    )

def generate_all_subtitled_videos(
    project_folder,
    story_count
):

    output_folder = os.path.join(
        project_folder,
        "subtitled_videos"
    )

    os.makedirs(
        output_folder,
        exist_ok=True
    )

    for number in range(
        1,
        story_count + 1
    ):

        video_file = os.path.join(
            project_folder,
            "videos",
            f"story_{number:02d}_video.mp4"
        )

        subtitle_file = os.path.join(
            project_folder,
            "subtitles",
            f"story_{number:02d}.srt"
        )

        output_file = os.path.join(
            output_folder,
            f"story_{number:02d}_subtitled.mp4"
        )

        if not os.path.exists(video_file):
            print(
                f"STORY {number} HAS NO VIDEO "
                f"- SKIPPING"
            )
            continue

        if not os.path.exists(subtitle_file):
            print(
                f"STORY {number} HAS NO SUBTITLES "
                f"- SKIPPING"
            )
            continue

        if os.path.exists(output_file):
            print(
                f"SUBTITLED VIDEO ALREADY EXISTS "
                f"- SKIPPING: {output_file}"
            )
            continue

        create_subtitled_video(
            video_file,
            subtitle_file,
            output_file
        )

def create_subtitle_preview(
    video_file,
    subtitle_file,
    output_file
):

    subtitle_path = os.path.abspath(
        subtitle_file
    )

    subtitle_path = subtitle_path.replace(
        "\\",
        "/"
    )

    subtitle_path = subtitle_path.replace(
        ":",
        "\\:"
    )

    command = [
        "ffmpeg",
        "-y",

        "-i", video_file,

        "-t", "20",

        "-vf",
        (
            f"subtitles='{subtitle_path}':"
            "force_style='"
            "FontName=Arial,"
            "FontSize=22,"
            "Alignment=2,"
            "MarginV=55,"
            "Outline=2,"
            "Shadow=1"
            "'"
        ),

        "-c:v", "libx264",
        "-preset", "veryfast",

        "-c:a", "copy",

        output_file
    ]

    subprocess.run(
        command,
        check=True
    )

    print(
        f"SUBTITLE PREVIEW SAVED: {output_file}"
    )

def should_retry_transcription_error(
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





