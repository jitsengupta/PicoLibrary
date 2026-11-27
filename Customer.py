"""
# Customer.py
# Domain model representing a customer and their contacts and activities
# Author: Hector Gonzalez
"""

from Log import *


class Customer:
    """
    Represents a customer retrieved from `GET .../customer/get_customers`,
    along with their associated `Contact` and `Activity` lists.

    Parameters:
    ----------
    id : str or int
        Customer identifier (stored as a string to preserve 39-digit ORDS IDs).
    name : str
        Customer name (or None).

    Examples:
    ---------
    1. cust = Customer(128485943572210253352629317186634790543, "Hector Gonzalez")
    2. Log.i(cust.get_name())
    """

    def __init__(self, id, name):
        """
        Initialize a Customer with an ID (stored as string), name, and empty
        contacts and activities lists.

        Parameters:
        ----------
        id : str or int
            Unique customer ID from ORDS.
        name : str
            Customer display name.

        Examples:
        ---------
        1. c = Customer("101", "Acme Corp")
        2. c = Customer(128485943572210253352629317186634790543, "Hector Gonzalez")
        """
        self._id = "" if id is None else str(id)
        self._name = "" if name is None else str(name)
        self._contacts = []
        self._activities = []

    def set_contacts(self, contacts):
        """
        Replace the customer's contact list.

        Parameters:
        ----------
        contacts : list
            List of `Contact` objects (None becomes `[]`).

        Examples:
        ---------
        1. cust.set_contacts([Contact("Barry Bruce", "CFO", "295-732-1037")])
        2. cust.set_contacts(None)
        """
        self._contacts = [] if contacts is None else list(contacts)

    def set_activities(self, activities):
        """
        Replace the customer's activity list.

        Parameters:
        ----------
        activities : list
            List of `Activity` objects (None becomes `[]`).

        Examples:
        ---------
        1. cust.set_activities([Activity("Demo Grounds", "Conference", "2026-10-13T00:00:00Z", "Miami")])
        2. cust.set_activities(None)
        """
        self._activities = [] if activities is None else list(activities)

    def get_id(self):
        """
        Return the customer ID as a string.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. cid = cust.get_id()
        2. Log.i(cust.get_id())
        """
        return self._id

    def get_name(self):
        """
        Return the customer name.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. name = cust.get_name()
        2. Log.i(cust.get_name())
        """
        return self._name

    def get_contacts(self):
        """
        Return the list of `Contact` objects for this customer.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. contacts = cust.get_contacts()
        2. Log.i(f"Count: {len(cust.get_contacts())}")
        """
        return self._contacts

    def get_activities(self):
        """
        Return the list of `Activity` objects for this customer.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. activities = cust.get_activities()
        2. Log.i(f"Count: {len(cust.get_activities())}")
        """
        return self._activities

    def has_activities(self):
        """
        Return `True` if this customer has at least one activity, `False` otherwise.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. if cust.has_activities(): ...
        2. Log.i(f"Has activities: {cust.has_activities()}")
        """
        return len(self._activities) > 0

    def __str__(self):
        """
        Return a summary string `"name (C:<number of contacts> A:<number of activities>)"`.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. str(cust) -> "Hector Gonzalez (C:0 A:1)"
        2. Log.i(str(cust))
        """
        return f"{self._name} (C:{len(self._contacts)} A:{len(self._activities)})"


if __name__ == "__main__":
    from Contact import Contact
    from Activity import Activity

    c1 = Customer(128485943572210253352629317186634790543, "Hector Gonzalez")
    assert c1.get_id() == "128485943572210253352629317186634790543"
    assert c1.get_name() == "Hector Gonzalez"

    c1.set_contacts([])
    c1.set_activities([
        Activity("Demo Grounds", "Conference", "2026-10-13T00:00:00Z", "Miami")
    ])
    Log.i(f"Customer 1: {c1} | id={c1.get_id()} | has_activities={c1.has_activities()}")
    assert len(c1.get_contacts()) == 0
    assert len(c1.get_activities()) == 1
    assert c1.has_activities() is True
    assert str(c1) == "Hector Gonzalez (C:0 A:1)"

    c2 = Customer(42, "No Activity Client")
    c2.set_contacts([Contact("Barry Bruce", "CFO", "295-732-1037")])
    Log.i(f"Customer 2: {c2} | id={c2.get_id()} | has_activities={c2.has_activities()}")
    assert c2.has_activities() is False
    assert str(c2) == "No Activity Client (C:1 A:0)"

    Log.i("Testing complete - Customer")
