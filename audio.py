import os
from config import TTS_MODEL, DEFAULT_VOICE_ID
import subprocess
import tempfile
from retry import run_with_retry
from state import load_project_state
from cost_tracking import (
    record_cost_event,
    get_usage_totals
)

def should_retry_elevenlabs_error(
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
        "ConnectionError",
        "TimeoutError",
        "RateLimitError"
    }:
        return True

    return False

def split_story_for_tts(text, max_chars=9000):

    paragraphs = text.split("\n\n")

    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:

        if len(current_chunk) + len(paragraph) + 2 <= max_chars:
            current_chunk += paragraph + "\n\n"

        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())

            current_chunk = paragraph + "\n\n"

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks

def audio_file_is_valid(audio_file_path):

    if not os.path.exists(audio_file_path):
        return False

    if os.path.getsize(audio_file_path) < 1000:
        return False

    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        audio_file_path
    ]

    try:

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )

        duration = float(
            result.stdout.strip()
        )

        return duration > 1

    except (
        subprocess.CalledProcessError,
        ValueError
    ):

        return False

def all_story_audio_is_valid(
    project_folder,
    story_count
):

    found_story = False

    for number in range(
        1,
        story_count + 1
    ):

        story_file = os.path.join(
            project_folder,
            f"story_{number:02d}.txt"
        )

        if not os.path.exists(
            story_file
        ):
            return False

        found_story = True

        audio_file = os.path.join(
            project_folder,
            "audio",
            f"story_{number:02d}.mp3"
        )

        if not audio_file_is_valid(
            audio_file
        ):
            return False

    return found_story

def generate_story_audio(
    elevenlabs,
    project_folder,
    story_file_path,
    audio_file_path,
    voice_id=DEFAULT_VOICE_ID,
    force=False
):

    if os.path.exists(audio_file_path) and not force:

        if audio_file_is_valid(
            audio_file_path
        ):

            print(
                f"AUDIO ALREADY EXISTS AND IS VALID "
                f"- SKIPPING: {audio_file_path}"
            )

            return

        print(
            f"INVALID AUDIO FOUND "
            f"- DELETING: {audio_file_path}"
        )

        os.remove(
            audio_file_path
        )

    with open(
        story_file_path,
        "r",
        encoding="utf-8"
    ) as file:

        story_text = file.read()

    story_text = story_text.replace("**", "")
    story_text = story_text.replace("__", "")
    story_text = story_text.replace("`", "")

    chunks = split_story_for_tts(
        story_text
    )

    print(
        f"\nGENERATING AUDIO: "
        f"{story_file_path}"
    )

    print(
        f"Chunks: {len(chunks)}"
    )

    audio_folder = os.path.dirname(
        audio_file_path
    )

    os.makedirs(
        audio_folder,
        exist_ok=True
    )

    with tempfile.TemporaryDirectory(
        dir=audio_folder
    ) as temp_folder:

        chunk_files = []

        for index, chunk in enumerate(
            chunks,
            start=1
        ):

            print(
                f"Generating audio chunk "
                f"{index}/{len(chunks)}..."
            )

            chunk_file = os.path.join(
                temp_folder,
                f"chunk_{index:03d}.mp3"
            )

            def generate_audio_chunk():

                audio_stream = (
                    elevenlabs.text_to_speech.convert(
                        voice_id=voice_id,
                        text=chunk,
                        model_id=TTS_MODEL,
                        output_format="mp3_44100_128"
                    )
                )

                return b"".join(
                    audio_stream
                )

            audio_data = run_with_retry(
                generate_audio_chunk,
                attempts=3,
                delay_seconds=2,
                should_retry=should_retry_elevenlabs_error
            )

            with open(
                chunk_file,
                "wb"
            ) as output_file:

                output_file.write(
                    audio_data
                )

            chunk_files.append(
                chunk_file
            )

            record_cost_event(
                project_folder,
                "elevenlabs",
                "narration_chunk",
                0.0,
                usage_amount=len(chunk),
                usage_unit="characters",
                model=TTS_MODEL
            )

        concat_file = os.path.join(
            temp_folder,
            "concat.txt"
        )

        with open(
            concat_file,
            "w",
            encoding="utf-8"
        ) as file:

            for chunk_file in chunk_files:

                safe_path = chunk_file.replace(
                    "\\",
                    "/"
                )

                file.write(
                    f"file '{safe_path}'\n"
                )

        temporary_output = os.path.join(
            temp_folder,
            "combined.mp3"
        )

        command = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_file,
            "-c:a",
            "libmp3lame",
            "-b:a",
            "128k",
            temporary_output
        ]

        subprocess.run(
            command,
            check=True
        )

        # Validate the newly generated audio
        # BEFORE replacing the original file.
        if not audio_file_is_valid(temporary_output):
            raise RuntimeError(
                f"Generated audio failed validation: "
                f"{temporary_output}"
            )

        # Only replace the original after validation succeeds.
        os.replace(
            temporary_output,
            audio_file_path
        )

    print(
        f"AUDIO SAVED AND VALIDATED: "
        f"{audio_file_path}"
    )

def generate_all_story_audio(
    elevenlabs,
    project_folder,
    story_count,
    voice_id=DEFAULT_VOICE_ID,
    force=False
):
    
    state = load_project_state(project_folder)

    audio_state = state["stages"].get("audio", {})

    force = (
        force
        or audio_state.get("rebuild_required", False)
    )

    audio_folder = os.path.join(
        project_folder,
        "audio"
    )

    os.makedirs(
        audio_folder,
        exist_ok=True
    )

        # Check every story before making paid API calls.
    missing_or_empty_stories = []

    for number in range(1, story_count + 1):
        story_name = f"story_{number:02d}.txt"

        story_path = os.path.join(
            project_folder,
            story_name
        )

        if (
            not os.path.isfile(story_path)
            or os.path.getsize(story_path) == 0
        ):
            missing_or_empty_stories.append(story_name)

    if missing_or_empty_stories:
        raise RuntimeError(
            "Cannot generate narration. "
            "Missing or empty stories: "
            + ", ".join(missing_or_empty_stories)
        )
    
    for number in range(1, story_count + 1):

        story_file_path = os.path.join(
            project_folder,
            f"story_{number:02d}.txt"
        )

        audio_file_path = os.path.join(
            audio_folder,
            f"story_{number:02d}.mp3"
        )


        generate_story_audio(
            elevenlabs,
            project_folder,
            story_file_path,
            audio_file_path,
            voice_id=voice_id,
            force=force
        )
    
        usage_totals = get_usage_totals(
        project_folder
    )

    elevenlabs_characters = usage_totals.get(
        (
            "elevenlabs",
            "characters"
        ),
        0
    )

    print(
        f"\nELEVENLABS CHARACTERS USED: "
        f"{elevenlabs_characters:,}"
    )   







