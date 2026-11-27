"""
# ViewState.py
# View state constants and name helper for the CRM kiosk UI
# Author: Hector Gonzalez
"""

from Log import *


class ViewState:
    """
    Enumeration-like constants class representing the current UI screen state
    for the IoT CRM kiosk (MicroPython does not provide the standard `enum` module).

    Attributes:
    ----------
    CLIENT_LIST : int
        State 0 - browsing the top-level list of customers.
    CONTACTS_VIEW : int
        State 1 - browsing contacts for the currently selected customer.
    ACTIVITIES_VIEW : int
        State 2 - browsing activities for the currently selected customer.
    NAMES : tuple
        Human-readable names indexed by state value.

    Examples:
    ---------
    1. state = ViewState.CLIENT_LIST
    2. Log.i(ViewState.name(state))
    """

    CLIENT_LIST = 0
    CONTACTS_VIEW = 1
    ACTIVITIES_VIEW = 2
    NAMES = ("CLIENT_LIST", "CONTACTS_VIEW", "ACTIVITIES_VIEW")

    @staticmethod
    def name(state):
        """
        Return the readable name for a given view state integer.

        Parameters:
        ----------
        state : int
            The view state value (0, 1, or 2).

        Examples:
        ---------
        1. ViewState.name(ViewState.CLIENT_LIST) -> "CLIENT_LIST"
        2. ViewState.name(99) -> "UNKNOWN"
        """
        if isinstance(state, int) and 0 <= state < len(ViewState.NAMES):
            return ViewState.NAMES[state]
        return "UNKNOWN"


if __name__ == "__main__":
    states = (
        ViewState.CLIENT_LIST,
        ViewState.CONTACTS_VIEW,
        ViewState.ACTIVITIES_VIEW,
    )
    for s in states:
        Log.i(f"State {s}: {ViewState.name(s)}")
    Log.i(f"Invalid state 99: {ViewState.name(99)}")

    assert len(set(states)) == 3, "ViewState values must be distinct"
    assert ViewState.name(ViewState.CLIENT_LIST) == "CLIENT_LIST"
    assert ViewState.name(ViewState.CONTACTS_VIEW) == "CONTACTS_VIEW"
    assert ViewState.name(ViewState.ACTIVITIES_VIEW) == "ACTIVITIES_VIEW"
    assert ViewState.name(-1) == "UNKNOWN"

    Log.i("Testing complete - ViewState")
