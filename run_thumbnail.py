import os
import json

from dotenv import load_dotenv
from openai import OpenAI

from thumbnail import (
    generate_thumbnail_image,
    create_final_thumbnail
)

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

project_folder = os.path.join(
    "output",
    "10_chilling_stories_of_technology_that_knew_too_much"
)

thumbnail_plan_file = os.path.join(
    project_folder,
    "thumbnail_plan.json"
)

with open(
    thumbnail_plan_file,
    "r",
    encoding="utf-8"
) as file:
    thumbnail_plan = json.load(file)

generate_thumbnail_image(
    client,
    project_folder,
    thumbnail_plan
)

create_final_thumbnail(
    project_folder,
    thumbnail_plan
)

print("\nTHUMBNAIL COMPLETE")