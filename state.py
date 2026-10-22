import os
import json
from datetime import datetime, timezone
import shutil

STATE_FILE_NAME = "project_state.json"


DEFAULT_STAGES = [
    "idea",
    "story_selection",
    "stories",
    "visual_plans",
    "scene_images",
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

STAGE_DEPENDENCIES = {
    "story_selection": {"idea"},
    "stories": {"story_selection"},
    "visual_plans": {"stories"},
    "scene_images": {"visual_plans"},
    "audio": {"stories"},
    "subtitles": {"audio", "stories"},
    "story_videos": {"audio", "scene_images"},
    "subtitled_videos": {"story_videos", "subtitles"},
    "transitions": {"subtitled_videos"},
    "combined_video": {"transitions"},
    "ambience": {"combined_video"},
    "metadata": {"stories"},
    "thumbnail_plan": {"metadata"},
    "thumbnail_image": {"thumbnail_plan"},
    "thumbnail_final": {"thumbnail_plan", "thumbnail_image"},
    "shorts": {"ambience", "subtitles", "metadata"},
    "cleanup": {"shorts", "thumbnail_final"}
}


def get_downstream_stages(stage):

    if stage not in DEFAULT_STAGES:
        raise ValueError(
            f"Unknown pipeline stage: {stage}"
        )

    affected = {stage}

    while True:

        new_stages = {
            name
            for name, dependencies in STAGE_DEPENDENCIES.items()
            if dependencies & affected
        }

        if new_stages.issubset(affected):
            break

        affected.update(new_stages)

    return [
        name
        for name in DEFAULT_STAGES
        if name in affected and name != stage
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


def load_project_state(
    project_folder
):

    state_path = get_state_path(
        project_folder
    )

    backup_path = state_path + ".bak"

    if not os.path.exists(state_path):

        if os.path.exists(backup_path):

            print(
                "\nSTATE FILE MISSING "
                "- RESTORING FROM BACKUP..."
            )

            shutil.copy2(
                backup_path,
                state_path
            )

            with open(
                state_path,
                "r",
                encoding="utf-8"
            ) as file:
                return json.load(file)

        return create_project_state(
            project_folder
        )

    try:

        with open(
            state_path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(
                file
            )

    except (
        json.JSONDecodeError,
        OSError
    ):

        print(
            "\nSTATE FILE COULD NOT BE READ"
        )

        if os.path.exists(
            backup_path
        ):

            print(
                "RESTORING STATE FROM BACKUP..."
            )

            with open(
                backup_path,
                "r",
                encoding="utf-8"
            ) as file:

                state = json.load(
                    file
                )

            restore_temp_path = (
                state_path + ".restore.tmp"
            )

            shutil.copy2(
                backup_path,
                restore_temp_path
            )

            os.replace(
                restore_temp_path,
                state_path
            )

            return state

        raise


def save_project_state(
    project_folder,
    state
):

    state["updated_at"] = get_timestamp()

    state_path = get_state_path(
        project_folder
    )

    temp_path = state_path + ".tmp"
    backup_path = state_path + ".bak"

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

    if os.path.exists(
        state_path
    ):

        shutil.copy2(
            state_path,
            backup_path
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
    if status == "complete":
        state["stages"][stage]["rebuild_required"] = False

    if status in {
        "pending",
        "running",
        "failed"
    }:
        state["status"] = "in_progress"

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
    force=False,
    on_skip=None,
    completion_check=None,
    **kwargs
):

    if (
        skip_if_complete
        and not force
        and stage_is_complete(
            project_folder,
            stage
        )
    ):

        output_is_valid = True

        if completion_check is not None:

            output_is_valid = completion_check()

        if output_is_valid:

            print(
                f"\n{stage.upper()} ALREADY COMPLETE "
                f"- SKIPPING"
            )

            if on_skip is not None:
                return on_skip()

            return None

        print(
            f"\n{stage.upper()} WAS MARKED COMPLETE "
            f"BUT OUTPUT IS MISSING OR INVALID "
            f"- RERUNNING"
        )

        set_stage_status(
            project_folder,
            stage,
            "pending"
        )

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

        if (
            completion_check is not None
            and not completion_check()
        ):
            raise RuntimeError(
                f"{stage.upper()} finished, "
                f"but its output is missing or invalid"
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
    
    state = load_project_state(
        project_folder
    )

    stage_info = state["stages"].get(
        stage,
        {}
    )

    if (
        stage_info.get("status") in {
            "stale",
            "running",
            "failed"
        }
        or stage_info.get("rebuild_required", False)
    ):
        print(
            f"STAGE {stage.upper()} IS STALE "
            f"- EXISTING OUTPUT CANNOT BE REUSED"
        )
        return False

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

def mark_downstream_stale(
    project_folder,
    changed_stage
):

    downstream_stages = get_downstream_stages(
        changed_stage
    )

    state = load_project_state(
        project_folder
    )

    for stage in downstream_stages:

        if stage not in state["stages"]:
            state["stages"][stage] = {
                "status": "pending",
                "error": None
            }

        state["stages"][stage]["status"] = "stale"
        state["stages"][stage]["error"] = None
        state["stages"][stage]["rebuild_required"] = True

    if downstream_stages:
        state["status"] = "in_progress"

    save_project_state(
        project_folder,
        state
    )

    print(
        f"\nINVALIDATED {len(downstream_stages)} "
        f"DOWNSTREAM STAGES"
    )

    return downstream_stages

def final_video_can_be_reused(
    project_folder,
    final_video_file
):

    if (
        not os.path.isfile(final_video_file)
        or os.path.getsize(final_video_file) <= 1000
    ):
        return False

    state = load_project_state(
        project_folder
    )

    required_stages = [
        "stories",
        "audio",
        "subtitles",
        "visual_plans",
        "scene_images",
        "story_videos",
        "subtitled_videos",
        "transitions",
        "combined_video",
        "ambience"
    ]

    for stage in required_stages:

        status = state["stages"].get(
            stage, {}
        ).get("status")

        if status in {
            "stale",
            "failed",
            "running"
        }:
            return False

    return True




