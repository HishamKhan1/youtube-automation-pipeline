import os
import json

def save_video_info(
    output_folder,
    video_idea,
    selected_stories,
    all_story_ideas,
    attempted_story_ids=None,
    narrator_profiles=None,
    channel_slug=None
):

    if attempted_story_ids is None:
        attempted_story_ids = set()
        
    if narrator_profiles is None:
        narrator_profiles = {}
        
        
    video_info = {
        "video_idea": video_idea,
        "selected_stories": selected_stories,
        "all_story_ideas": all_story_ideas,
        "attempted_story_ids": list(attempted_story_ids),
        "narrator_profiles": narrator_profiles,
        "channel_slug": channel_slug
    }

    file_path = os.path.join(
        output_folder,
        "video_info.json"
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            video_info,
            file,
            indent=2
        )

def load_video_info(output_folder):

    file_path = os.path.join(
        output_folder,
        "video_info.json"
    )

    if not os.path.exists(file_path):
        return None

    with open(file_path, "r", encoding="utf-8") as file:
        video_info = json.load(file)

    return video_info

def completed_story_files_are_valid(
    project_folder,
    selected_stories
):

    final_video = os.path.join(
        project_folder,
        "final_video_complete.mp4"
    )

    # Support older finished projects that
    # were created before the marker existed.
    if (
        os.path.exists(final_video)
        and os.path.getsize(final_video) > 1000
    ):

        if not selected_stories:
            return False

        for number in range(
            1,
            len(selected_stories) + 1
        ):

            story_file = os.path.join(
                project_folder,
                f"story_{number:02d}.txt"
            )

            if (
                not os.path.isfile(story_file)
                or os.path.getsize(story_file) == 0
            ):
                return False

        return True
    completion_marker = os.path.join(
        project_folder,
        "stories_complete.marker"
    )

    if not os.path.exists(
        completion_marker
    ):
        return False

    found_story = False

    for number, story in enumerate(
        selected_stories,
        start=1
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

        if os.path.getsize(
            story_file
        ) == 0:
            return False

    return found_story

def get_completed_stories(
    project_folder,
    selected_stories
):

    completed_stories = []

    for number, story in enumerate(
        selected_stories,
        start=1
    ):

        story_file = os.path.join(
            project_folder,
            f"story_{number:02d}.txt"
        )

        if os.path.exists(story_file):
            completed_stories.append(
                story
            )

    return completed_stories

def choose_project_folder():

    output_folder = "output"

    projects = []

    for folder_name in os.listdir(
        output_folder
    ):

        project_folder = os.path.join(
            output_folder,
            folder_name
        )

        video_info_file = os.path.join(
            project_folder,
            "video_info.json"
        )

        if (
            os.path.isdir(project_folder)
            and os.path.exists(video_info_file)
        ):
            projects.append(
                project_folder
            )

    if not projects:
        print("\nNO VIDEO PROJECTS FOUND.")
        return None

    print("\nVIDEO PROJECTS:")

    for index, project in enumerate(
        projects,
        start=1
    ):

        print(
            f"{index}. "
            f"{os.path.basename(project)}"
        )

    choice = input(
        "\nChoose project: "
    )

    try:
        project_index = int(choice) - 1

        return projects[
            project_index
        ]

    except:
        print(
            "INVALID PROJECT SELECTION."
        )

        return None





















