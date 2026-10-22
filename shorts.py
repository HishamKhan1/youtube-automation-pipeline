import os
import subprocess
import tempfile
import shutil
import re
from pathlib import Path


def timestamp_to_seconds(timestamp):
    match = re.fullmatch(
        r"(\d{2}):([0-5]\d):([0-5]\d),(\d{3})",
        timestamp.strip()
    )

    if not match:
        raise ValueError(
            f"Invalid subtitle timestamp: {timestamp}"
        )

    hours, minutes, seconds, milliseconds = (
        map(int, match.groups())
    )

    return (
        hours * 3600
        + minutes * 60
        + seconds
        + milliseconds / 1000
    )


def load_srt_cues(subtitle_file):
    path = Path(subtitle_file)

    if not path.is_file():
        raise FileNotFoundError(
            f"Subtitle file missing: {path}"
        )

    content = path.read_text(
        encoding="utf-8-sig"
    ).replace("\r\n", "\n").strip()

    cues = []

    for block in re.split(r"\n\s*\n", content):
        lines = [
            line.strip()
            for line in block.splitlines()
            if line.strip()
        ]

        if not lines:
            continue

        timing_index = 1 if lines[0].isdigit() else 0

        if (
            timing_index >= len(lines)
            or "-->" not in lines[timing_index]
        ):
            raise ValueError("Invalid SRT subtitle block")

        start_text, end_text = (
            lines[timing_index].split("-->", 1)
        )

        start = timestamp_to_seconds(start_text)
        end = timestamp_to_seconds(end_text)

        text = " ".join(
            lines[timing_index + 1:]
        )

        if end <= start or not text:
            raise ValueError("Invalid subtitle cue")

        cues.append({
            "start": start,
            "end": end,
            "text": text
        })

    if not cues:
        raise ValueError(
            f"No subtitle cues found: {path}"
        )

    return cues

def select_story_short(
    cues,
    min_duration=25,
    max_duration=55
):
    if not 0 < min_duration <= max_duration:
        raise ValueError("Invalid Short duration limits")

    if not cues:
        return None

    suspense_words = {
        "heard", "saw", "scream", "shadow",
        "whisper", "door", "behind", "alone",
        "someone", "something", "missing",
        "dead", "blood", "footsteps",
        "knocking", "watched", "breathing",
        "disappeared", "never", "wrong"
    }

    best_clip = None

    for start_index, first in enumerate(cues):

        parts = []

        for end_index in range(start_index, len(cues)):

            last = cues[end_index]
            duration = last["end"] - first["start"]

            if duration > max_duration:
                break

            parts.append(last["text"])

            if duration < min_duration:
                continue

            text = " ".join(parts)

            words = set(
                re.findall(r"\b\w+\b", text.lower())
            )

            suspense_score = len(
                words & suspense_words
            ) * 3

            natural_end = last["text"].rstrip().endswith(
                (".", "!", "?")
            )

            natural_start = (
                start_index == 0
                or cues[start_index - 1]["text"]
                    .rstrip().endswith((".", "!", "?"))
            )

            score = (
                suspense_score
                + (4 if natural_start else 0)
                + (4 if natural_end else 0)
                - abs(duration - 45) * 0.1
            )

            if (
                best_clip is None
                or score > best_clip["score"]
            ):
                best_clip = {
                    "start": first["start"],
                    "end": last["end"],
                    "duration": duration,
                    "text": text,
                    "score": score
                }

    return best_clip

def select_project_shorts(
    project_folder,
    story_count,
    min_shorts=3,
    max_shorts=5
):
    if not 1 <= min_shorts <= max_shorts:
        raise ValueError("Invalid Shorts count limits")

    candidates = []

    for number in range(1, story_count + 1):

        subtitle_file = (
            Path(project_folder)
            / "subtitles"
            / f"story_{number:02d}.srt"
        )

        cues = load_srt_cues(subtitle_file)

        clip = select_story_short(cues)

        if clip is None:
            continue

        candidates.append({
            **clip,
            "story_number": number,
            "subtitle_file": str(subtitle_file)
        })

    if len(candidates) < min_shorts:
        raise RuntimeError(
            f"Only {len(candidates)} eligible Shorts found. "
            f"At least {min_shorts} required."
        )

    candidates.sort(
        key=lambda clip: (
            -clip["score"],
            clip["story_number"]
        )
    )

    return candidates[:max_shorts]

def render_vertical_short(
    source_video,
    output_file,
    start,
    end,
    width=1080,
    height=1920
):
    source_video = Path(source_video)
    output_file = Path(output_file)

    if not source_video.is_file():
        raise FileNotFoundError(source_video)

    if not 0 <= start < end:
        raise ValueError("Invalid clip timestamps")

    if (
        width <= 0
        or height <= 0
        or width % 2
        or height % 2
    ):
        raise ValueError("Invalid video dimensions")

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    duration = end - start

    # Render to a temporary file so the existing
    # Short survives if FFmpeg fails.
    with tempfile.TemporaryDirectory(
        dir=output_file.parent
    ) as temp_folder:

        temporary_output = (
            Path(temp_folder) / "short.mp4"
        )

        video_filter = (
            f"scale={width}:{height}:"
            "force_original_aspect_ratio=increase,"
            f"crop={width}:{height},"
            "setsar=1,"
            "fps=30"
        )

        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-y",
            "-ss", f"{start:.3f}",
            "-i", str(source_video),
            "-t", f"{duration:.3f}",
            "-vf", video_filter,
            "-map", "0:v:0",
            "-map", "0:a:0",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "160k",
            "-movflags", "+faststart",
            str(temporary_output)
        ]

        subprocess.run(
            command,
            check=True
        )

        if (
            not temporary_output.is_file()
            or temporary_output.stat().st_size <= 1000
        ):
            raise RuntimeError(
                "Short rendering produced no valid-sized output"
            )

        os.replace(
            temporary_output,
            output_file
        )

    print(f"VERTICAL SHORT SAVED: {output_file}")

    return str(output_file)

def seconds_to_srt_timestamp(seconds):
    if seconds < 0:
        raise ValueError("Negative subtitle timestamp")

    milliseconds = round(seconds * 1000)

    hours, milliseconds = divmod(
        milliseconds, 3600000
    )
    minutes, milliseconds = divmod(
        milliseconds, 60000
    )
    secs, milliseconds = divmod(
        milliseconds, 1000
    )

    return (
        f"{hours:02d}:{minutes:02d}:"
        f"{secs:02d},{milliseconds:03d}"
    )

def create_short_subtitles(
    source_srt,
    output_srt,
    clip_start,
    clip_end
):
    if not 0 <= clip_start < clip_end:
        raise ValueError("Invalid clip timestamps")

    cues = load_srt_cues(source_srt)
    blocks = []

    for cue in cues:
        start = max(cue["start"], clip_start)
        end = min(cue["end"], clip_end)

        if end <= start:
            continue

        relative_start = start - clip_start
        relative_end = end - clip_start

        blocks.append(
            f"{len(blocks) + 1}\n"
            f"{seconds_to_srt_timestamp(relative_start)}"
            " --> "
            f"{seconds_to_srt_timestamp(relative_end)}\n"
            f"{cue['text']}"
        )

    if not blocks:
        raise RuntimeError(
            "No subtitles overlap the selected Short"
        )

    output_path = Path(output_srt)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Preserve existing subtitles if saving fails.
    with tempfile.TemporaryDirectory(
        dir=output_path.parent
    ) as folder:

        temporary_file = Path(folder) / "short.srt"

        temporary_file.write_text(
            "\n\n".join(blocks) + "\n",
            encoding="utf-8"
        )

        os.replace(
            temporary_file,
            output_path
        )

    return str(output_path)

def burn_short_captions(
    vertical_video,
    subtitle_file,
    output_file
):
    video = Path(vertical_video).resolve()
    subtitles = Path(subtitle_file).resolve()
    output = Path(output_file).resolve()

    if not video.is_file():
        raise FileNotFoundError(video)

    # Validate subtitle contents before rendering.
    # Validate SRT or ASS subtitles.
    subtitle_type = subtitles.suffix.lower()

    if subtitle_type == ".srt":
        load_srt_cues(subtitles)

    elif subtitle_type == ".ass":
        if not subtitles.is_file():
            raise FileNotFoundError(subtitles)

        content = subtitles.read_text(
            encoding="utf-8-sig"
        )

        if (
            "[Events]" not in content
            or "Dialogue:" not in content
        ):
            raise ValueError(
                "Invalid or empty ASS subtitles"
            )

    else:
        raise ValueError(
            f"Unsupported subtitle format: {subtitle_type}"
        )

    if video == output:
        raise ValueError(
            "Captioned output must differ from source video"
        )

    output.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    style = (
        "FontName=Arial,"
        "FontSize=14,"
        "Bold=1,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "BorderStyle=1,"
        "Outline=1.5,"
        "Shadow=0,"
        "Alignment=2,"
        "MarginV=60"
    )
    

    with tempfile.TemporaryDirectory(
        dir=output.parent
    ) as folder:

        temp_folder = Path(folder)
        temp_subtitles = (
            temp_folder / f"captions{subtitle_type}"
        )
        temp_video = temp_folder / "captioned.mp4"

        # Using a simple local filename avoids
        # Windows drive-letter escaping issues.
        shutil.copyfile(
            subtitles,
            temp_subtitles
        )

        if subtitle_type == ".ass":
            # ASS files already contain their own styles.
            subtitle_filter = (
                "subtitles=filename=captions.ass"
            )
        else:
            subtitle_filter = (
                "subtitles=filename=captions.srt:"
                f"force_style='{style}'"
            )
        
        
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-y",
            "-i", str(video),
            "-vf", subtitle_filter,
            "-map", "0:v:0",
            "-map", "0:a:0",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            "-c:a", "copy",
            "-movflags", "+faststart",
            str(temp_video)
        ]

        subprocess.run(
            command,
            cwd=str(temp_folder),
            check=True
        )

        if (
            not temp_video.is_file()
            or temp_video.stat().st_size <= 1000
        ):
            raise RuntimeError(
                "Caption rendering produced an invalid-sized file"
            )

        os.replace(temp_video, output)

    print(f"CAPTIONED SHORT SAVED: {output}")

    return str(output)

def split_cues_for_shorts(cues, max_words=4):
    if max_words < 2:
        raise ValueError("max_words must be at least 2")

    short_cues = []

    for cue in cues:
        start = cue["start"]
        end = cue["end"]
        words = cue["text"].split()

        if end <= start:
            raise ValueError("Invalid subtitle cue duration")

        if not words:
            continue

        # Calculate how many caption groups we need.
        group_count = (
            len(words) + max_words - 1
        ) // max_words

        # Distribute words evenly across groups.
        base_size, extra = divmod(
            len(words),
            group_count
        )

        position = 0

        for index in range(group_count):
            group_size = base_size + (
                1 if index < extra else 0
            )

            next_position = position + group_size

            group_start = start + (
                (end - start)
                * position / len(words)
            )

            group_end = start + (
                (end - start)
                * next_position / len(words)
            )

            short_cues.append({
                "start": group_start,
                "end": group_end,
                "text": " ".join(
                    words[position:next_position]
                )
            })

            position = next_position

    return short_cues

def seconds_to_ass_timestamp(seconds):
    if seconds < 0:
        raise ValueError("Negative timestamp")

    centiseconds = round(seconds * 100)

    hours, remainder = divmod(
        centiseconds, 360000
    )
    minutes, remainder = divmod(
        remainder, 6000
    )
    secs, cs = divmod(remainder, 100)

    return f"{hours}:{minutes:02d}:{secs:02d}.{cs:02d}"


def create_styled_short_ass(
    source_srt,
    output_ass
):
    cues = load_srt_cues(source_srt)
    groups = split_cues_for_shorts(
        cues, max_words=4
    )

    # More dramatic words receive higher priority.
    emphasis = {
        "scream": 100,
        "blood": 100,
        "dead": 100,
        "footsteps": 95,
        "whisper": 90,
        "shadow": 90,
        "behind": 85,
        "knocking": 85,
        "alone": 80,
        "door": 60,
        "heard": 30,
        "someone": 20
    }

    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Horror,Arial,72,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,4,0,2,80,80,460,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    dialogue_lines = []

    for group in groups:
        words = group["text"].split()

        def word_score(word):
            normalized = re.sub(
                r"[^a-z]", "", word.lower()
            )
            return emphasis.get(normalized, 0)

        scores = [
            word_score(word) for word in words
        ]

        highlighted_index = (
            scores.index(max(scores))
            if scores and max(scores) > 0
            else None
        )

        formatted = []

        for index, word in enumerate(words):
            # Prevent source text from injecting ASS tags.
            clean = re.sub(
                r"[{}\\]", "", word
            ).upper()

            if index == highlighted_index:
                clean = (
                    r"{\1c&H00D7FF&}"
                    + clean
                    + r"{\1c&H00FFFFFF&}"
                )

            formatted.append(clean)

        caption = " ".join(formatted)

        animation = (
            r"{\fad(80,80)"
            r"\fscx92\fscy92"
            r"\t(0,120,\fscx100\fscy100)}"
        )

        start = seconds_to_ass_timestamp(
            group["start"]
        )
        end = seconds_to_ass_timestamp(
            group["end"]
        )

        dialogue_lines.append(
            f"Dialogue: 0,{start},{end},"
            f"Horror,,0,0,0,,"
            f"{animation}{caption}"
        )

    output = Path(output_ass)
    output.parent.mkdir(
        parents=True, exist_ok=True
    )

    if Path(source_srt).resolve() == output.resolve():
        raise ValueError("Output cannot overwrite source")

    with tempfile.TemporaryDirectory(
        dir=output.parent
    ) as folder:
        temporary = Path(folder) / "captions.ass"

        temporary.write_text(
            header + "\n".join(dialogue_lines) + "\n",
            encoding="utf-8"
        )

        os.replace(temporary, output)

    return str(output)

def render_selected_project_short(
    project_folder,
    clip,
    short_number
):
    project = Path(project_folder)

    story_number = clip["story_number"]
    start = clip["start"]
    end = clip["end"]

    if (
        not isinstance(story_number, int)
        or story_number < 1
        or not isinstance(short_number, int)
        or short_number < 1
    ):
        raise ValueError("Invalid story or Short number")

    if not 0 <= start < end:
        raise ValueError("Invalid Short timestamps")

    source_video = (
        project / "videos"
        / f"story_{story_number:02d}_video.mp4"
    )

    source_srt = (
        project / "subtitles"
        / f"story_{story_number:02d}.srt"
    )

    # Validate inputs before rendering.
    for source in (source_video, source_srt):
        if not source.is_file():
            raise FileNotFoundError(source)

    shorts_folder = project / "shorts"
    assets_folder = shorts_folder / "assets"

    assets_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    name = (
        f"short_{short_number:02d}"
        f"_story_{story_number:02d}"
    )

    vertical_video = (
        assets_folder / f"{name}_vertical.mp4"
    )

    short_srt = (
        assets_folder / f"{name}.srt"
    )

    styled_ass = (
        assets_folder / f"{name}.ass"
    )

    final_video = (
        shorts_folder / f"{name}.mp4"
    )

    print(
        f"\nCREATING SHORT {short_number} "
        f"FROM STORY {story_number}"
    )

    # 1. Shift subtitles to Short timestamps.
    create_short_subtitles(
        source_srt,
        short_srt,
        start,
        end
    )

    # 2. Create animated captions.
    create_styled_short_ass(
        short_srt,
        styled_ass
    )

    # 3. Crop story visuals into vertical format.
    render_vertical_short(
        source_video,
        vertical_video,
        start,
        end
    )

    # 4. Burn animated captions into the video.
    burn_short_captions(
        vertical_video,
        styled_ass,
        final_video
    )

    print(f"SHORT COMPLETE: {final_video}")

    return str(final_video)



