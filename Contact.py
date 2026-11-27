"""
# Contact.py
# Domain model representing a customer contact from the ORDS CRM API
# Author: Hector Gonzalez
"""

from Log import *


class Contact:
    """
    Represents a contact person associated with a customer.
    Data is populated from `GET .../customer/get_contacts/{cust_id}`,
    storing **name**, **title**, and **phone** while normalizing `None` values to `""`.

    Parameters:
    ----------
    name : str
        Full name of the contact (or None).
    title : str
        Job title of the contact (or None).
    phone : str
        Phone number of the contact (or None).

    Examples:
    ---------
    1. c = Contact("Barry Bruce", "CFO", "295-732-1037")
    2. Log.i(c.get_name())
    """

    def __init__(self, name, title, phone):
        """
        Initialize a Contact instance, converting any None field to an empty string.

        Parameters:
        ----------
        name : str
            Contact's full name.
        title : str
            Contact's job title.
        phone : str
            Contact's phone number.

        Examples:
        ---------
        1. c1 = Contact("Barry Bruce", "CFO", "295-732-1037")
        2. c2 = Contact(None, None, None)
        """
        self._name = "" if name is None else str(name)
        self._title = "" if title is None else str(title)
        self._phone = "" if phone is None else str(phone)

    def get_name(self):
        """
        Return the contact's name.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. name = contact.get_name()
        2. Log.i(contact.get_name())
        """
        return self._name

    def get_title(self):
        """
        Return the contact's job title.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. title = contact.get_title()
        2. Log.i(contact.get_title())
        """
        return self._title

    def get_phone(self):
        """
        Return the contact's phone number.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. phone = contact.get_phone()
        2. Log.i(contact.get_phone())
        """
        return self._phone

    def __str__(self):
        """
        Return a formatted string representation `"name (title)"`.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. str(Contact("Barry Bruce", "CFO", "295-732-1037")) -> "Barry Bruce (CFO)"
        2. Log.i(str(contact))
        """
        return f"{self._name} ({self._title})"


if __name__ == "__main__":
    c1 = Contact("Barry Bruce", "CFO", "295-732-1037")
    Log.i(f"Contact 1: {c1} | phone: {c1.get_phone()}")
    assert c1.get_name() == "Barry Bruce"
    assert c1.get_title() == "CFO"
    assert c1.get_phone() == "295-732-1037"
    assert str(c1) == "Barry Bruce (CFO)"

    c2 = Contact(None, None, None)
    Log.i(f"Contact 2 (None fields): {c2} | phone: '{c2.get_phone()}'")
    assert c2.get_name() == ""
    assert c2.get_title() == ""
    assert c2.get_phone() == ""
    assert str(c2) == " ()"

    Log.i("Testing complete - Contact")
