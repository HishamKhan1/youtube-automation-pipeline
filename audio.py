import os
from config import TTS_MODEL, DEFAULT_VOICE_ID

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

def generate_story_audio(
    elevenlabs,
    story_file_path,
    audio_file_path,
    voice_id=DEFAULT_VOICE_ID
):

    if os.path.exists(audio_file_path):
        print(f"AUDIO ALREADY EXISTS - SKIPPING: {audio_file_path}")
        return

    with open(story_file_path, "r", encoding="utf-8") as f:
        story_text = f.read()
    
    story_text = story_text.replace("**", "")
    story_text = story_text.replace("__", "")
    story_text = story_text.replace("`", "")

    chunks = split_story_for_tts(story_text)

    print(f"\nGENERATING AUDIO: {story_file_path}")
    print(f"Chunks: {len(chunks)}")

    with open(audio_file_path, "wb") as output_file:

        for index, chunk in enumerate(chunks, start=1):

            print(
                f"Generating audio chunk "
                f"{index}/{len(chunks)}..."
            )

            audio = elevenlabs.text_to_speech.convert(
                voice_id=voice_id,
                text=chunk,
                model_id=TTS_MODEL,
                output_format="mp3_44100_128"
            )

            for audio_chunk in audio:
                if audio_chunk:
                    output_file.write(audio_chunk)

    print(f"AUDIO SAVED: {audio_file_path}")

def generate_all_story_audio(
    elevenlabs,
    project_folder,
    story_count
):

    audio_folder = os.path.join(
        project_folder,
        "audio"
    )

    os.makedirs(
        audio_folder,
        exist_ok=True
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

        if not os.path.exists(story_file_path):
            print(
                f"STORY {number} HAS NO FINAL FILE - SKIPPING AUDIO"
            )
            continue

        generate_story_audio(
            elevenlabs,
            story_file_path,
            audio_file_path
        )







