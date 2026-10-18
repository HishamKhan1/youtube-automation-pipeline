import time


def run_with_retry(
    action,
    *args,
    attempts=3,
    delay_seconds=2,
    should_retry=None,
    **kwargs
):

    last_error = None

    for attempt in range(
        1,
        attempts + 1
    ):

        try:

            return action(
                *args,
                **kwargs
            )

        except Exception as error:

            last_error = error

            if (
                should_retry is not None
                and not should_retry(error)
            ):
                raise
            
            print(
                f"\nATTEMPT "
                f"{attempt}/{attempts} FAILED"
            )

            print(
                f"ERROR: {error}"
            )

            if attempt < attempts:
                
                
                
                print(
                    f"RETRYING IN "
                    f"{delay_seconds} SECONDS..."
                )

                time.sleep(
                    delay_seconds
                )

    raise last_error