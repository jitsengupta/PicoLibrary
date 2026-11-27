"""
# Activity.py
# Domain model representing a customer activity from the ORDS CRM API
# Author: Hector Gonzalez
"""

from Log import *


class Activity:
    """
    Represents a CRM activity associated with a customer.
    Data is populated from `GET .../customer/get_activities/{cust_id}`,
    storing **name**, **activity_type**, **activity_date**, and **location**
    while normalizing `None` values to `""`.

    Parameters:
    ----------
    name : str
        Name of the activity (or None).
    activity_type : str
        Type/category of the activity (or None).
    activity_date : str
        ISO-8601 date string of the activity (or None).
    location : str
        Location where the activity takes place (or None).

    Examples:
    ---------
    1. a = Activity("Demo Grounds", "Conference", "2026-10-13T00:00:00Z", "Miami")
    2. Log.i(a.get_short_date())
    """

    def __init__(self, name, activity_type, activity_date, location):
        """
        Initialize an Activity instance, converting any None field to an empty string.

        Parameters:
        ----------
        name : str
            Activity name.
        activity_type : str
            Activity type/category.
        activity_date : str
            Activity date string (e.g. "2026-10-13T00:00:00Z").
        location : str
            Activity location.

        Examples:
        ---------
        1. a1 = Activity("Demo Grounds", "Conference", "2026-10-13T00:00:00Z", "Miami")
        2. a2 = Activity(None, None, None, None)
        """
        self._name = "" if name is None else str(name)
        self._activity_type = "" if activity_type is None else str(activity_type)
        self._activity_date = "" if activity_date is None else str(activity_date)
        self._location = "" if location is None else str(location)

    def get_name(self):
        """
        Return the activity name.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. name = activity.get_name()
        2. Log.i(activity.get_name())
        """
        return self._name

    def get_activity_type(self):
        """
        Return the activity type.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. t = activity.get_activity_type()
        2. Log.i(activity.get_activity_type())
        """
        return self._activity_type

    def get_activity_date(self):
        """
        Return the full activity date string as stored.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. d = activity.get_activity_date()
        2. Log.i(activity.get_activity_date())
        """
        return self._activity_date

    def get_location(self):
        """
        Return the activity location.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. loc = activity.get_location()
        2. Log.i(activity.get_location())
        """
        return self._location

    def get_short_date(self):
        """
        Return the first 10 characters of the activity date (YYYY-MM-DD),
        or `""` if the date is empty.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. activity.get_short_date() -> "2026-10-13"
        2. Activity(None, None, None, None).get_short_date() -> ""
        """
        if not self._activity_date:
            return ""
        return self._activity_date[:10]

    def __str__(self):
        """
        Return a formatted string representation `"name - activity_type"`.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. str(a) -> "Demo Grounds - Conference"
        2. Log.i(str(a))
        """
        return f"{self._name} - {self._activity_type}"


if __name__ == "__main__":
    a1 = Activity("Demo Grounds", "Conference", "2026-10-13T00:00:00Z", "Miami")
    Log.i(f"Activity 1: {a1} | short_date: {a1.get_short_date()} | loc: {a1.get_location()}")
    assert a1.get_name() == "Demo Grounds"
    assert a1.get_activity_type() == "Conference"
    assert a1.get_activity_date() == "2026-10-13T00:00:00Z"
    assert a1.get_location() == "Miami"
    assert a1.get_short_date() == "2026-10-13"
    assert str(a1) == "Demo Grounds - Conference"

    a2 = Activity(None, None, None, None)
    Log.i(f"Activity 2 (None fields): '{a2}' | short_date: '{a2.get_short_date()}'")
    assert a2.get_name() == ""
    assert a2.get_activity_type() == ""
    assert a2.get_activity_date() == ""
    assert a2.get_location() == ""
    assert a2.get_short_date() == ""
    assert str(a2) == " - "

    Log.i("Testing complete - Activity")
