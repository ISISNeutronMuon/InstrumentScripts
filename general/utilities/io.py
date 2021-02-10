"""
Input / Output utilities
"""
from genie_python import genie as g


def alert_on_error(error_msg: str, prompt_user: bool):
    print(error_msg)
    """
    Sends a given error message as an alert an optionally interrupts execution to prompt the user whether the script
    should continue being executed.

    Args:
        error_msg: The message for the error to alert users to.
        prompt_user: If false, continue script. If True, prompt user to either stop or continue script.
    """
    g.alerts.send(error_msg)
    if prompt_user:
        while True:
            user_response = input("Continue execution? [Y/N]\n").upper()
            if user_response == "Y":
                break
            elif user_response == "N":
                raise KeyboardInterrupt
            else:
                print("Please type in 'Y' or 'N' as a response.")
