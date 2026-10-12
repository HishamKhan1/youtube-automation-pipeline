# Automated YouTube Horror Video Generator

A modular Python automation pipeline that generates complete long-form horror story videos for YouTube.

The system handles story ideation, script generation, quality control, AI narration, subtitle synchronization, video rendering, background ambience, transitions, metadata, and thumbnail generation.

The goal of the project is to automate as much of the video production workflow as possible while keeping each part of the pipeline modular and reusable.

## Features

- AI-generated video concepts and story premises
- Automatic story selection and replacement
- Story quality evaluation and revision
- Narrator profile generation
- Long-form fictional horror story generation
- ElevenLabs text-to-speech narration
- Automatic audio chunking for long stories
- Word-level subtitle timestamps
- Story-to-transcript word alignment
- FFmpeg video rendering
- Looping background footage
- Story title transition screens
- Background rain ambience
- Automatic video concatenation
- AI-generated YouTube titles and descriptions
- AI-generated thumbnail concepts and backgrounds
- Pillow-based thumbnail text rendering
- Resume support for unfinished projects
- Separate finalization workflow for completed projects

## Project Structure

```text
youtube_generator/
│
├── main.py
├── pipeline.py
├── project.py
├── story_generation.py
├── audio.py
├── subtitles.py
├── video.py
├── thumbnail.py
├── metadata.py
├── visuals.py
│
├── assets/
│   ├── backgrounds/
│   └── ambience/
│
├── output/
├── requirements.txt
├── .env
└── .gitignore
```

### Modules

**main.py**  
Application entry point and command-line menu.

**pipeline.py**  
Coordinates the final video production pipeline.

**project.py**  
Handles project saving, loading, resume functionality, and project selection.

**story_generation.py**  
Handles video concepts, story premises, narrator profiles, story generation, evaluation, and revision.

**audio.py**  
Handles ElevenLabs narration generation and long-text audio chunking.

**subtitles.py**  
Generates word-level timestamps, aligns story text with transcription results, creates subtitles, and burns subtitles into video.

**video.py**  
Handles FFmpeg rendering, story videos, transitions, concatenation, and background ambience.

**thumbnail.py**  
Generates thumbnail concepts, AI backgrounds, and final text overlays.

**metadata.py**  
Generates YouTube titles and descriptions from the completed stories.

**visuals.py**  
Contains experimental visual-scene planning functionality for future dynamic visual generation.

## Pipeline

```text
Video Idea
    ↓
Story Premises
    ↓
Story Selection
    ↓
Premise Quality Control
    ↓
Narrator Profile
    ↓
Story Generation
    ↓
Story Quality Control
    ↓
Text-to-Speech
    ↓
Word-Level Transcription
    ↓
Subtitle Alignment
    ↓
Story Video Rendering
    ↓
Transitions
    ↓
Video Concatenation
    ↓
Background Ambience
    ↓
YouTube Metadata
    ↓
Thumbnail Generation
    ↓
Final Video
```

## Requirements

- Python
- FFmpeg
- OpenAI API key
- ElevenLabs API key

Python dependencies are included in `requirements.txt`.

Install them with:

```bash
pip install -r requirements.txt
```

FFmpeg must also be installed separately and available from the system command line.

## Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
```

The `.env` file is excluded from Git and should never be committed.

## Running the Program

Run:

```bash
python main.py
```

The program provides three main options:

```text
YOUTUBE VIDEO GENERATOR

1. Create new video
2. Resume existing video
3. Finalize video
```

### Create New Video

Starts a new project and generates the video idea, stories, narration, subtitles, and video assets.

### Resume Existing Video

Loads a previously saved project and continues from its existing progress.

### Finalize Video

Takes completed story videos and produces the final upload-ready video, metadata, and thumbnail.

## Output

Each generated video receives its own folder inside `output/`.

A completed project can contain:

```text
final_video_complete.mp4
youtube_metadata.json
thumbnail_final.png
video_info.json
story files
audio files
subtitle files
transition videos
intermediate video files
```

Generated media inside `output/` is ignored by Git.

## Technologies

- Python
- OpenAI API
- ElevenLabs API
- FFmpeg
- Pillow
- JSON
- Regular Expressions
- SequenceMatcher
- Git

## Technical Highlights

One of the more complex parts of the project is subtitle synchronization.

Instead of simply displaying raw transcription text, the system compares the original generated story against word-level transcription results and aligns the two. This allows the final subtitles to preserve the original script while using timing information from the generated narration.

The project also uses a quality-control pipeline where generated story premises and completed stories can be evaluated and revised before progressing through the production process.

Projects are saved throughout generation so interrupted runs can be resumed instead of restarting the entire workflow.

## Testing

The project includes unit tests for core non-API functionality, including:

- TTS text chunking
- Subtitle word normalization
- Story-to-transcription word alignment

Run the full test suite with:

```bash
python -m unittest discover -s tests
```

Current test suite: **7 passing tests**.

## Current Status

The core automated production pipeline is functional.

The current version generates an upload-ready video, thumbnail, title, and description. Uploading and publishing to YouTube is currently performed manually.

Future development may include:

- Dynamic AI-generated visual scenes
- Additional background video strategies
- Automated cleanup and archiving of intermediate files
- Configuration files for models, voices, and rendering settings
- Automated testing
- Optional YouTube upload integration

## Author

Hisham Khan

Started September 2026.