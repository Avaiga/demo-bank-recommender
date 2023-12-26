"""Entry point for the bank recommender application"""

from taipy.gui import Gui, State, notify


def prompt_notif(state: State) -> None:
    """
    Sends a notification to the user when the button is clicked.

    Args:
        - state: The current state of the application.
    """
    notify(state, "info", "Hello!")


page = """
# Bank Recommender Application

<|Notify|button|on_action=prompt_notif|>
"""

if __name__ == "__main__":
    gui = Gui(page)
    gui.run(dark_mode=True, debug=True, use_reloader=True)
