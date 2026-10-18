import os
import json
from datetime import datetime, timezone


STATE_FILE_NAME = "project_state.json"


DEFAULT_STAGES = [
    "idea",
    "story_selection",
    "stories",
    "audio",
    "subtitles",
    "story_videos",
    "subtitled_videos",
    "transitions",
    "combined_video",
    "ambience",
    "metadata",
    "thumbnail_plan",
    "thumbnail_image",
    "thumbnail_final",
    "shorts",
    "cleanup",
]


def get_timestamp():
    return datetime.now(timezone.utc).isoformat()


def get_state_path(project_folder):
    return os.path.join(
        project_folder,
        STATE_FILE_NAME
    )


def create_project_state(project_folder):

    os.makedirs(
        project_folder,
        exist_ok=True
    )

    stages = {}

    for stage in DEFAULT_STAGES:
        stages[stage] = {
            "status": "pending",
            "error": None
        }

    state = {
        "version": 1,
        "status": "in_progress",
        "created_at": get_timestamp(),
        "updated_at": get_timestamp(),
        "stages": stages
    }

    save_project_state(
        project_folder,
        state
    )

    return state


def load_project_state(project_folder):

    state_path = get_state_path(
        project_folder
    )

    if not os.path.exists(state_path):
        return create_project_state(
            project_folder
        )

    with open(
        state_path,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def save_project_state(
    project_folder,
    state
):

    state["updated_at"] = get_timestamp()

    state_path = get_state_path(
        project_folder
    )

    temp_path = state_path + ".tmp"

    with open(
        temp_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            state,
            file,
            indent=4
        )

    os.replace(
        temp_path,
        state_path
    )


def set_stage_status(
    project_folder,
    stage,
    status,
    error=None
):

    state = load_project_state(
        project_folder
    )

    if stage not in state["stages"]:
        state["stages"][stage] = {
            "status": "pending",
            "error": None
        }

    state["stages"][stage]["status"] = status
    state["stages"][stage]["error"] = error

    save_project_state(
        project_folder,
        state
    )


def stage_is_complete(
    project_folder,
    stage
):

    state = load_project_state(
        project_folder
    )

    stage_info = state["stages"].get(
        stage
    )

    if stage_info is None:
        return False

    return stage_info["status"] == "complete"

def mark_project_complete(
    project_folder
):

    state = load_project_state(
        project_folder
    )

    state["status"] = "complete"

    save_project_state(
        project_folder,
        state
    )
    
def run_stage(
    project_folder,
    stage,
    action,
    *args,
    skip_if_complete=True,
    on_skip=None,
    **kwargs
):

    if (
        skip_if_complete
        and stage_is_complete(
            project_folder,
            stage
        )
    ):

        print(
            f"\n✓ {stage.upper()} ALREADY COMPLETE "
            f"- SKIPPING"
        )

        if on_skip is not None:
            return on_skip()

        return None

    print(
        f"\n▶ STARTING STAGE: "
        f"{stage.upper()}"
    )

    set_stage_status(
        project_folder,
        stage,
        "running"
    )

    try:

        result = action(
            *args,
            **kwargs
        )

    except Exception as error:

        set_stage_status(
            project_folder,
            stage,
            "failed",
            error=str(error)
        )

        print(
            f"\n✗ STAGE FAILED: "
            f"{stage.upper()}"
        )

        print(
            f"ERROR: {error}"
        )

        raise

    set_stage_status(
        project_folder,
        stage,
        "complete"
    )

    print(
        f"✓ STAGE COMPLETE: "
        f"{stage.upper()}"
    )

    return result 
    
def complete_stage_if_file_exists(
    project_folder,
    stage,
    file_path
):

    if not os.path.exists(
        file_path
    ):
        return False

    if not stage_is_complete(
        project_folder,
        stage
    ):

        set_stage_status(
            project_folder,
            stage,
            "complete"
        )

        print(
            f"✓ FOUND EXISTING OUTPUT "
            f"- MARKED {stage.upper()} COMPLETE"
        )

    return True   
    
    
    
    
    
    
    
    