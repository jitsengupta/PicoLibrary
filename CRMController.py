"""
# CRMController.py
# Main controller for the IoT CRM kiosk on Raspberry Pi Pico 2 W
# Author: Hector Gonzalez
"""

import time
import gc
from Log import *
from ViewState import ViewState
from Customer import Customer
from Contact import Contact
from Activity import Activity


class CRMController:
    """
    Controller that orchestrates the IoT CRM kiosk: connects to Wi-Fi,
    retrieves customers, contacts, and activities from the Oracle ORDS REST API,
    displays views on a 16x2 I2C LCD, and drives an 8-LED NeoPixel ring and
    passive buzzer in response to 4 navigation buttons.

    Parameters:
    ----------
    None

    Examples:
    ---------
    1. controller = CRMController()
    2. controller.run()
    """

    BASE_URL = "https://iacademy.oracle.com/ords/ism6205/customer"
    USE_OPTION_A = True      # Option A: load everything at startup
    LCD_WIDTH = 16

    def __init__(self):
        """
        Initialize the LCD, buzzer, light strip, network interface, buttons,
        and initial state/index attributes.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. ctrl = CRMController()
        2. ctrl.update_view()
        """
        from Displays import LCDDisplay
        from Buzzer import PassiveBuzzer
        from LightStrip import LightStrip
        from Lights import GREEN, RED, BLUE
        from Net import Net
        from Button import Button

        self._GREEN = GREEN
        self._RED = RED
        self._BLUE = BLUE

        self._customers = []
        self._current_idx = 0
        self._detail_idx = 0
        self._state = ViewState.CLIENT_LIST
        self._events = []

        self._display = LCDDisplay(sda=0, scl=1)
        self._display.clear()
        self._display.showText("CRM Kiosk", 0, 0)
        self._display.showText("Starting...", 1, 0)

        self._buzzer = PassiveBuzzer(15)
        self._lightstrip = LightStrip(pin=2, numleds=8)
        self._net = Net()

        self._btn_next = Button(10, "next", handler=self)
        self._btn_prev = Button(11, "prev", handler=self)
        self._btn_select = Button(12, "select", handler=self)
        self._btn_back = Button(13, "back", handler=self)

    def _fit(self, text):
        """
        Convert text to a string and truncate to `LCD_WIDTH` (16 characters).

        Parameters:
        ----------
        text : str
            Input text to fit on a single 16-column LCD line.

        Examples:
        ---------
        1. self._fit("Very Long Customer Name") -> "Very Long Custom"
        """
        if text is None:
            return ""
        return str(text)[:self.LCD_WIDTH]

    def buttonPressed(self, name):
        """
        IRQ-safe button press callback invoked by `Button._callback`.
        Queues up to 5 button names in `self._events` for the main loop.

        Parameters:
        ----------
        name : str
            Name of the button that was pressed ("next", "prev", "select", "back").

        Examples:
        ---------
        1. ctrl.buttonPressed("next")
        2. ctrl.buttonPressed("select")
        """
        if len(self._events) < 5:
            self._events.append(name)

    def buttonReleased(self, name):
        """
        IRQ-safe button release callback required by `Button._callback`.
        Performs no action on release.

        Parameters:
        ----------
        name : str
            Name of the button that was released.

        Examples:
        ---------
        1. ctrl.buttonReleased("next")
        """
        pass

    def connect_wifi(self):
        """
        Connect to Wi-Fi using credentials from `secrets.py`.
        Updates the LCD, NeoPixel ring, and buzzer on failure.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. if ctrl.connect_wifi(): ...
        """
        import secrets

        self._display.clear()
        self._display.showText(self._fit("Connecting WiFi"), 0, 0)
        self._display.showText(self._fit(secrets.WIFI_SSID), 1, 0)

        try:
            pwd = secrets.WIFI_PASSWORD
            self._net.connect(secrets.WIFI_SSID, pwd)
            return True
        except RuntimeError as e:
            Log.e(f"WiFi connection failed: {e}")
            self._display.clear()
            self._display.showText("WiFi failed", 0, 0)
            self._display.showText("Check secrets.py", 1, 0)
            self._lightstrip.setColor(self._RED)
            self._buzzer.beep(tone=300, duration=500)
            return False

    def _fetch_items(self, url):
        """
        Fetch JSON from an ORDS endpoint and return its `"items"` list,
        or `[]` if the request fails or has no `"items"` key.

        Parameters:
        ----------
        url : str
            Full ORDS REST API endpoint URL.

        Examples:
        ---------
        1. items = self._fetch_items(self.BASE_URL + "/get_customers")
        """
        result = self._net.getJson(url)
        if not isinstance(result, dict):
            Log.e(f"Failed to fetch items from {url}")
            return []
        items = result.get("items")
        if not isinstance(items, list):
            Log.e(f"No valid items list in response from {url}")
            return []
        return items

    def load_all_upfront(self):
        """
        Option A startup loader: retrieve all customers and each customer's
        contacts and activities upfront, showing progress on the LCD and
        NeoPixel ring.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. ok = ctrl.load_all_upfront()
        """
        items = self._fetch_items(self.BASE_URL + "/get_customers")
        if not items:
            self._display.clear()
            self._display.showText("No customers", 0, 0)
            return False

        self._customers = []
        total = len(items)

        for i in range(total):
            item = items[i]
            cust = Customer(item.get("id"), item.get("customer_name"))

            self._display.clear()
            self._display.showText(self._fit(f"Loading {i + 1}/{total}"), 0, 0)
            self._display.showText(self._fit(cust.get_name()), 1, 0)

            progress = max(1, ((i + 1) * 8) // total)
            self._lightstrip.setColor(self._BLUE, numPixels=progress)

            raw_contacts = self._fetch_items(
                self.BASE_URL + "/get_contacts/" + cust.get_id()
            )
            contacts = []
            for c in raw_contacts:
                contacts.append(
                    Contact(c.get("name"), c.get("title"), c.get("phone"))
                )
            cust.set_contacts(contacts)

            raw_activities = self._fetch_items(
                self.BASE_URL + "/get_activities/" + cust.get_id()
            )
            activities = []
            for a in raw_activities:
                activities.append(
                    Activity(
                        a.get("name"),
                        a.get("activity_type"),
                        a.get("activity_date"),
                        a.get("location"),
                    )
                )
            cust.set_activities(activities)

            self._customers.append(cust)
            gc.collect()

        self._lightstrip.off()
        self._buzzer.beep(tone=1000, duration=100)
        return True

    def load_customers_only(self):
        """
        Option B startup loader: retrieve only the customer list without
        fetching per-customer contacts or activities yet.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. ok = ctrl.load_customers_only()
        """
        self._display.clear()
        self._display.showText("Loading clients", 0, 0)
        items = self._fetch_items(self.BASE_URL + "/get_customers")
        if not items:
            self._display.clear()
            self._display.showText("No customers", 0, 0)
            return False

        self._customers = []
        for item in items:
            cust = Customer(item.get("id"), item.get("customer_name"))
            self._customers.append(cust)
        gc.collect()
        self._lightstrip.off()
        self._buzzer.beep(tone=1000, duration=100)
        return True

    def load_details(self, cust):
        """
        Option B on-demand loader: fetch contacts and activities for a single
        `Customer` when selected.

        Parameters:
        ----------
        cust : Customer
            The customer whose contacts and activities should be loaded.

        Examples:
        ---------
        1. ctrl.load_details(cust)
        """
        if cust is None:
            return
        self._display.clear()
        self._display.showText("Loading...", 0, 0)
        self._display.showText(self._fit(cust.get_name()), 1, 0)

        raw_contacts = self._fetch_items(
            self.BASE_URL + "/get_contacts/" + cust.get_id()
        )
        contacts = []
        for c in raw_contacts:
            contacts.append(
                Contact(c.get("name"), c.get("title"), c.get("phone"))
            )
        cust.set_contacts(contacts)

        raw_activities = self._fetch_items(
            self.BASE_URL + "/get_activities/" + cust.get_id()
        )
        activities = []
        for a in raw_activities:
            activities.append(
                Activity(
                    a.get("name"),
                    a.get("activity_type"),
                    a.get("activity_date"),
                    a.get("location"),
                )
            )
        cust.set_activities(activities)
        gc.collect()

    def _current_customer(self):
        """
        Return the currently highlighted `Customer`, or `None` if `_customers` is empty.
        """
        if not self._customers:
            return None
        return self._customers[self._current_idx]

    def next_item(self):
        """
        Advance to the next customer (in `CLIENT_LIST`) or next contact/activity
        (in `CONTACTS_VIEW` / `ACTIVITIES_VIEW`) with wrap-around, then refresh
        the LCD and hardware feedback.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. ctrl.next_item()
        """
        self._buzzer.beep(tone=1200, duration=40)
        if not self._customers:
            return

        if self._state == ViewState.CLIENT_LIST:
            self._current_idx = (self._current_idx + 1) % len(self._customers)
        elif self._state == ViewState.CONTACTS_VIEW:
            contacts = self._current_customer().get_contacts()
            if contacts:
                self._detail_idx = (self._detail_idx + 1) % len(contacts)
        elif self._state == ViewState.ACTIVITIES_VIEW:
            activities = self._current_customer().get_activities()
            if activities:
                self._detail_idx = (self._detail_idx + 1) % len(activities)

        self.update_view()
        self.update_feedback()

    def prev_item(self):
        """
        Move to the previous customer (in `CLIENT_LIST`) or previous contact/activity
        (in `CONTACTS_VIEW` / `ACTIVITIES_VIEW`) with wrap-around, then refresh
        the LCD and hardware feedback.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. ctrl.prev_item()
        """
        self._buzzer.beep(tone=1200, duration=40)
        if not self._customers:
            return

        if self._state == ViewState.CLIENT_LIST:
            self._current_idx = (self._current_idx - 1) % len(self._customers)
        elif self._state == ViewState.CONTACTS_VIEW:
            contacts = self._current_customer().get_contacts()
            if contacts:
                self._detail_idx = (self._detail_idx - 1) % len(contacts)
        elif self._state == ViewState.ACTIVITIES_VIEW:
            activities = self._current_customer().get_activities()
            if activities:
                self._detail_idx = (self._detail_idx - 1) % len(activities)

        self.update_view()
        self.update_feedback()

    def select(self):
        """
        Handle the Select button:
        - In `CLIENT_LIST`: open the highlighted customer's `CONTACTS_VIEW`
          (loading details first if `USE_OPTION_A` is `False`) and trigger
          selection feedback on all 8 LEDs and the buzzer.
        - In `CONTACTS_VIEW` or `ACTIVITIES_VIEW`: delegate to `toggle_view()`.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. ctrl.select()
        """
        if not self._customers:
            return

        if self._state == ViewState.CLIENT_LIST:
            cust = self._current_customer()
            if not self.USE_OPTION_A:
                self.load_details(cust)
            self._state = ViewState.CONTACTS_VIEW
            self._detail_idx = 0
            self.update_view()
            self.update_feedback(selected=True)
        else:
            self.toggle_view()

    def toggle_view(self):
        """
        Switch between `CONTACTS_VIEW` and `ACTIVITIES_VIEW` for the currently
        selected customer, resetting `_detail_idx` to 0.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. ctrl.toggle_view()
        """
        if self._state == ViewState.CONTACTS_VIEW:
            self._state = ViewState.ACTIVITIES_VIEW
        elif self._state == ViewState.ACTIVITIES_VIEW:
            self._state = ViewState.CONTACTS_VIEW
        self._detail_idx = 0
        self._buzzer.beep(tone=900, duration=60)
        self.update_view()
        self.update_feedback()

    def go_back(self):
        """
        Handle the Back button:
        - In `CONTACTS_VIEW` or `ACTIVITIES_VIEW`: return to `CLIENT_LIST`.
        - In `CLIENT_LIST`: play a low short tone and remain in `CLIENT_LIST`.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. ctrl.go_back()
        """
        if self._state in (ViewState.CONTACTS_VIEW, ViewState.ACTIVITIES_VIEW):
            self._state = ViewState.CLIENT_LIST
            self._detail_idx = 0
            self._buzzer.beep(tone=600, duration=60)
        else:
            self._buzzer.beep(tone=300, duration=40)
        self.update_view()
        self.update_feedback()

    def update_view(self):
        """
        Render the current screen state (`CLIENT_LIST`, `CONTACTS_VIEW`, or
        `ACTIVITIES_VIEW`) onto the 16x2 I2C LCD, truncating each row to 16 chars.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. ctrl.update_view()
        """
        self._display.clear()
        cust = self._current_customer()
        if cust is None:
            self._display.showText("No customers", 0, 0)
            return

        if self._state == ViewState.CLIENT_LIST:
            total = len(self._customers)
            row0 = f"{self._current_idx + 1}/{total} {cust.get_name()}"
            c_count = len(cust.get_contacts())
            a_count = len(cust.get_activities())
            row1 = f"C:{c_count} A:{a_count}"
            self._display.showText(self._fit(row0), 0, 0)
            self._display.showText(self._fit(row1), 1, 0)

        elif self._state == ViewState.CONTACTS_VIEW:
            contacts = cust.get_contacts()
            if not contacts:
                self._display.showText(self._fit(cust.get_name()), 0, 0)
                self._display.showText("No contacts", 1, 0)
            else:
                if self._detail_idx >= len(contacts):
                    self._detail_idx = 0
                contact = contacts[self._detail_idx]
                row0 = f"{self._detail_idx + 1}/{len(contacts)} {contact.get_name()}"
                sub = contact.get_title() if contact.get_title() else contact.get_phone()
                self._display.showText(self._fit(row0), 0, 0)
                self._display.showText(self._fit(sub), 1, 0)

        elif self._state == ViewState.ACTIVITIES_VIEW:
            activities = cust.get_activities()
            if not activities:
                self._display.showText(self._fit(cust.get_name()), 0, 0)
                self._display.showText("No activities", 1, 0)
            else:
                if self._detail_idx >= len(activities):
                    self._detail_idx = 0
                act = activities[self._detail_idx]
                row0 = f"{self._detail_idx + 1}/{len(activities)} {act.get_name()}"
                row1 = f"{act.get_activity_type()} {act.get_short_date()}"
                self._display.showText(self._fit(row0), 0, 0)
                self._display.showText(self._fit(row1), 1, 0)

    def update_feedback(self, selected=False):
        """
        Update the 8-LED NeoPixel ring and passive buzzer according to whether
        the current customer has activities and whether the customer was just selected.

        Parameters:
        ----------
        selected : bool, optional
            `True` when transitioning into a customer's detail view to play
            the confirmation or warning chime (default: `False`).

        Examples:
        ---------
        1. ctrl.update_feedback()
        2. ctrl.update_feedback(selected=True)
        """
        cust = self._current_customer()
        if cust is None:
            self._lightstrip.off()
            return

        has_act = cust.has_activities()
        color = self._GREEN if has_act else self._RED

        if self._state == ViewState.CLIENT_LIST:
            self._lightstrip.setColor(color, numPixels=4)
        elif selected:
            self._lightstrip.setColor(color)
            if has_act:
                self._buzzer.beep(tone=880, duration=80)
                self._buzzer.beep(tone=1320, duration=120)
            else:
                self._buzzer.beep(tone=300, duration=300)
                time.sleep_ms(60)
                self._buzzer.beep(tone=300, duration=300)
        else:
            self._lightstrip.setColor(color)

    def _idle_forever(self):
        """
        Keep the current message visible on screen until interrupted.
        """
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self._lightstrip.off()
            self._buzzer.stop()
            self._display.clear()
            Log.i("CRM kiosk stopped")

    def run(self):
        """
        Connect to Wi-Fi, load CRM data from ORDS, display the first customer,
        and run the event loop dispatching queued button presses.

        Parameters:
        ----------
        None

        Examples:
        ---------
        1. CRMController().run()
        """
        if not self.connect_wifi():
            self._idle_forever()
            return

        loaded = (
            self.load_all_upfront()
            if self.USE_OPTION_A
            else self.load_customers_only()
        )
        if not loaded:
            self._idle_forever()
            return

        self._current_idx = 0
        self._detail_idx = 0
        self._state = ViewState.CLIENT_LIST
        self.update_view()
        self.update_feedback()

        try:
            while True:
                while self._events:
                    evt = self._events.pop(0)
                    Log.i(f"Handling button event: {evt} in state {ViewState.name(self._state)}")
                    if evt == "next":
                        self.next_item()
                    elif evt == "prev":
                        self.prev_item()
                    elif evt == "select":
                        self.select()
                    elif evt == "back":
                        self.go_back()
                time.sleep_ms(20)
        except KeyboardInterrupt:
            self._lightstrip.off()
            self._buzzer.stop()
            self._display.clear()
            Log.i("CRM kiosk stopped")


if __name__ == "__main__":
    ctrl = CRMController()

    c1 = Customer("1", "Hector Gonzalez")
    c1.set_contacts([])
    c1.set_activities([
        Activity("Demo Grounds", "Conference", "2026-10-13T00:00:00Z", "Miami")
    ])

    c2 = Customer("2", "Carlton Closets")
    c2.set_contacts([
        Contact("Barry Bruce", "CFO", "295-732-1037")
    ])
    c2.set_activities([])

    ctrl._customers = [c1, c2]
    ctrl._current_idx = 0
    ctrl._detail_idx = 0
    ctrl._state = ViewState.CLIENT_LIST

    Log.i("Step 0: Initial CLIENT_LIST view (Hector Gonzalez - has activities)")
    ctrl.update_view()
    ctrl.update_feedback()
    time.sleep(1)

    Log.i("Step 1: next -> Carlton Closets (no activities)")
    ctrl.next_item()
    time.sleep(1)

    Log.i("Step 2: select -> Carlton Closets CONTACTS_VIEW (Barry Bruce)")
    ctrl.select()
    time.sleep(1)

    Log.i("Step 3: select -> toggle to ACTIVITIES_VIEW (No activities)")
    ctrl.select()
    time.sleep(1)

    Log.i("Step 4: back -> return to CLIENT_LIST")
    ctrl.go_back()
    time.sleep(1)

    Log.i("Step 5: back -> already at CLIENT_LIST (low short beep)")
    ctrl.go_back()
    time.sleep(1)

    ctrl._lightstrip.off()
    Log.i("Testing complete - CRMController")
