import os
import json
from datetime import datetime, timezone


COST_FILE_NAME = "costs.json"
PENDING_COST_EVENTS = []
OPENAI_TEXT_PRICING = {
    "gpt-5-mini": {
        "input": 0.25,
        "output": 2.00
    },
    "gpt-5.4-mini": {
        "input": 0.75,
        "output": 4.50
    }
}
OPENAI_TRANSCRIPTION_PRICING = {
    "whisper-1": 0.006
}
OPENAI_IMAGE_PRICING = {
    "gpt-image-2.5-flare": {
        "text_input": 5.00,
        "image_input": 8.00,
        "image_output": 30.00
    }
}

def get_openai_text_price(
    model,
    token_type
):

    if not model:
        return None

    for model_name, pricing in (
        OPENAI_TEXT_PRICING.items()
    ):

        if model.startswith(
            model_name
        ):
            return pricing.get(
                token_type
            )

    return None

def get_cost_file_path(
    project_folder
):

    return os.path.join(
        project_folder,
        COST_FILE_NAME
    )

def load_cost_data(
    project_folder
):

    file_path = get_cost_file_path(
        project_folder
    )

    if not os.path.exists(
        file_path
    ):

        return {
            "events": [],
            "total_cost_usd": 0.0
        }

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(
            file
        )

def save_cost_data(
    project_folder,
    cost_data
):

    file_path = get_cost_file_path(
        project_folder
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            cost_data,
            file,
            indent=4
        )

def record_cost_event(
    project_folder,
    service,
    action,
    cost_usd,
    usage_amount=None,
    usage_unit=None,
    model=None
):

    event = {
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "service": service,
        "action": action,
        "cost_usd": round(
            cost_usd,
            6
        ),
        "usage_amount": usage_amount,
        "usage_unit": usage_unit,
        "model": model
    }

    if project_folder is None:

        PENDING_COST_EVENTS.append(
            event
        )

        return

    cost_data = load_cost_data(
        project_folder
    )

    cost_data["events"].append(
        event
    )

    cost_data["total_cost_usd"] = round(
        sum(
            item["cost_usd"]
            for item in cost_data["events"]
        ),
        6
    )

    save_cost_data(
        project_folder,
        cost_data
    )
    
def flush_pending_cost_events(
    project_folder
):

    global PENDING_COST_EVENTS

    if not PENDING_COST_EVENTS:
        return

    pending_events = PENDING_COST_EVENTS

    PENDING_COST_EVENTS = []

    for event in pending_events:

        record_cost_event(
            project_folder,
            event["service"],
            event["action"],
            event["cost_usd"],
            usage_amount=event.get(
                "usage_amount"
            ),
            usage_unit=event.get(
                "usage_unit"
            ),
            model=event.get(
                "model"
            )
        )
    
def get_usage_totals(
    project_folder
):

    cost_data = load_cost_data(
        project_folder
    )

    usage_totals = {}

    for event in cost_data["events"]:

        usage_amount = event.get(
            "usage_amount"
        )

        usage_unit = event.get(
            "usage_unit"
        )

        service = event.get(
            "service"
        )

        if (
            usage_amount is None
            or usage_unit is None
        ):
            continue

        key = (
            service,
            usage_unit
        )

        usage_totals[key] = (
            usage_totals.get(
                key,
                0
            )
            + usage_amount
        )

    return usage_totals   
    
def print_cost_summary(
    project_folder
):

    cost_data = load_cost_data(
        project_folder
    )

    usage_totals = get_usage_totals(
        project_folder
    )
    cost_totals = get_cost_totals_by_service(
        project_folder
    )

    print("\nPROJECT USAGE SUMMARY")

    for (
        service,
        usage_unit
    ), amount in usage_totals.items():

        print(
            f"{service.upper()} "
            f"{usage_unit}: "
            f"{amount:,}"
        )

    for service, cost in cost_totals.items():

        print(
            f"{service.upper()} COST: "
            f"${cost:.4f} USD"
        )
    
    print(
        f"ESTIMATED COST: "
        f"${cost_data['total_cost_usd']:.2f} USD"
    )
    
def record_openai_response_usage(
    project_folder,
    response,
    action
):

    usage = getattr(
        response,
        "usage",
        None
    )
    
    model = getattr(
        response,
        "model",
        None
    )

    if usage is None:
        return

    input_tokens = getattr(
        usage,
        "input_tokens",
        0
    )

    output_tokens = getattr(
        usage,
        "output_tokens",
        0
    )

    input_price = get_openai_text_price(
    model,
        "input"
    )

    output_price = get_openai_text_price(
        model,
        "output"
    )

    if input_tokens:

        input_cost = 0.0

        if input_price is not None:

            input_cost = (
                input_tokens
                / 1_000_000
                * input_price
            )

        record_cost_event(
            project_folder,
            "openai",
            action,
            input_cost,
            usage_amount=input_tokens,
            usage_unit="input_tokens",
            model=model
        )

    if output_tokens:

        output_cost = 0.0

        if output_price is not None:

            output_cost = (
                output_tokens
                / 1_000_000
                * output_price
            )

        record_cost_event(
            project_folder,
            "openai",
            action,
            output_cost,
            usage_amount=output_tokens,
            usage_unit="output_tokens",
            model=model
        )
    
def get_openai_image_price(
    model,
    usage_type
):

    if not model:
        return None

    for model_name, pricing in (
        OPENAI_IMAGE_PRICING.items()
    ):

        if model.startswith(
            model_name
        ):
            return pricing.get(
                usage_type
            )

    return None  
    
def record_openai_image_usage(
    project_folder,
    response,
    action,
    model
):

    usage = getattr(
        response,
        "usage",
        None
    )

    if usage is None:
        return

    input_details = getattr(
        usage,
        "input_tokens_details",
        None
    )

    text_input_tokens = 0
    image_input_tokens = 0

    if input_details is not None:

        text_input_tokens = getattr(
            input_details,
            "text_tokens",
            0
        )

        image_input_tokens = getattr(
            input_details,
            "image_tokens",
            0
        )

    image_output_tokens = getattr(
        usage,
        "output_tokens",
        0
    )

    if text_input_tokens:

        price = get_openai_image_price(
            model,
            "text_input"
        )

        cost = 0.0

        if price is not None:
            cost = (
                text_input_tokens
                / 1_000_000
                * price
            )

        record_cost_event(
            project_folder,
            "openai",
            action,
            cost,
            usage_amount=text_input_tokens,
            usage_unit="image_text_input_tokens",
            model=model
        )

    if image_input_tokens:

        price = get_openai_image_price(
            model,
            "image_input"
        )

        cost = 0.0

        if price is not None:
            cost = (
                image_input_tokens
                / 1_000_000
                * price
            )

        record_cost_event(
            project_folder,
            "openai",
            action,
            cost,
            usage_amount=image_input_tokens,
            usage_unit="image_input_tokens",
            model=model
        )

    if image_output_tokens:

        price = get_openai_image_price(
            model,
            "image_output"
        )

        cost = 0.0

        if price is not None:
            cost = (
                image_output_tokens
                / 1_000_000
                * price
            )

        record_cost_event(
            project_folder,
            "openai",
            action,
            cost,
            usage_amount=image_output_tokens,
            usage_unit="image_output_tokens",
            model=model
        )
    
def get_cost_totals_by_service(
    project_folder
):

    cost_data = load_cost_data(
        project_folder
    )

    totals = {}

    for event in cost_data["events"]:

        service = event.get(
            "service",
            "unknown"
        )

        cost = event.get(
            "cost_usd",
            0.0
        )

        totals[service] = (
            totals.get(
                service,
                0.0
            )
            + cost
        )

    return totals

def record_openai_transcription_usage(
    project_folder,
    duration_seconds,
    model="whisper-1"
):

    price_per_minute = (
        OPENAI_TRANSCRIPTION_PRICING.get(
            model
        )
    )

    if price_per_minute is None:
        return

    duration_minutes = (
        duration_seconds / 60
    )

    cost_usd = (
        duration_minutes
        * price_per_minute
    )

    record_cost_event(
        project_folder,
        "openai",
        "subtitle_transcription",
        cost_usd,
        usage_amount=duration_minutes,
        usage_unit="audio_minutes",
        model=model
    )











    