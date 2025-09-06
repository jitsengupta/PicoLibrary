"""
A basic template file for using the Model class in PicoLibrary
This will allow you to implement simple Statemodels with some basic
event-based transitions.
"""

# Import whatever Library classes you need - StateModel is obviously needed
# Counters imported for Timer functionality, Button imported for button events
import time
import random
from Log import *
from StateModel import *
from Counters import *

## You may want to remove any module you do not need from the imports below
from Button import *
from Lights import *
from Sensors import AnalogSensor

"""
This is the template for a Controller - you should rename this class to something
that is supported by your class diagram. This should associate with your other
classes, and any PicoLibrary classes. If you are using Buttons, you will implement
buttonPressed and buttonReleased.

To implement the state model, you will need to implement __init__ and 4 other methods
to support model start, stop, entry actions, exit actions, and state actions.

The following methods must be implemented:
__init__: create instances of your View and Business model classes, create an instance
of the StateModel with the necessary number of states and add the transitions, buttons
and timers that the StateModel needs

stateEntered(self, state, event) - Entry actions
stateLeft(self, state, event) - Exit actions
stateDo(self, state) - do Activities

# A couple other methods are available - but they can be left alone for most purposes

run(self) - runs the State Model - this will start at State 0 and drive the state model
stop(self) - stops the State Model - will stop processing events and stop the timers

This template currently implements a very simple state model that uses a button to
transition from state 0 to state 1 then a 5 second timer to go back to state 0.
"""

class MyController:

    def __init__(self):
        
        # STEP 1.
        # Instantiate whatever classes from your own model that you need to control
        # Handlers can now be set to None - we will add them to the model and it will
        # do the handling
        
        # ...
        self.led = Light(15, name='LED')

        # Instantiate a Model. Needs to have the number of states, self as the handler
        # You can also say debug=True to see some of the transitions on the screen
        # Here is a sample for a model with 4 states
        self._model = StateModel(3, self, debug=True)
        
        # Instantiate any Buttons that you want to process events from and add
        # them to the model
        self._button = Button(2, "button1", handler=None)        
        self._model.addButton(self._button)
        
        # add other buttons if needed. Note that button names must be distinct
        # for all buttons. Events will come back with [buttonname]_press and
        # [buttonname]_release

        # ...
        
        # Instantiate any sensor you need to process their trip/untrip events from
        # Events from sensors come back as sensorname_trip and sensorname_untrip

        self._pir = DigitalSensor(pin=9, name="pir", lowActive=False, handler=None)
        self._ldr = AnalogSensor(pin=26, name="ldr", lowActive=False)
        self._model.addSensor(self._pir)
        self._model.addSensor(self._ldr)

        # Add any timer you have. Multiple timers may be added but they must all
        # have distinct names. Events come back as [timername}_timeout
        self._timer = SoftwareTimer(name="timer1", handler=None)
        self._model.addTimer(self._timer)

        # Add any custom events as appropriate for your state model. e.g.
        # self._model.addCustomEvent("collision_detected")
        
        # Now add all the transitions from your state model. Any custom events
        # must be defined above first. You can have a state transition to another
        # state based on multiple events - which is why the eventlist is an array
        # Syntax: self._model.addTransition( SOURCESTATE, [eventlist], DESTSTATE)
        
        # some examples:
        self._model.addTransition(0, ["button1_press"], 1)
        self._model.addTransition(1, ["timer1_timeout"], 0)

        self._model.addTransition(0, ["pir_trip", "ldr_trip"], 2)
        self._model.addTransition(2, ["pir_untrip", "ldr_untrip"], 0)

        # etc.
    
    def stateEntered(self, state, event):
        """
        stateEntered - is the handler for performing entry actions
        You get the state number of the state that just entered
        Make sure actions here are quick
        """
        
        # If statements to do whatever entry/actions you need for
        # for states that have entry actions
        Log.d(f'State {state} entered on event {event}')
        if state == 0:
            # entry actions for state 0
            self.led.off()
        
        elif state == 1:
            # entry actions for state 1
            self.led.on()
            self._timer.start(5)
        
            
    def stateLeft(self, state, event):
        """
        stateLeft - is the handler for performing exit/actions
        You get the state number of the state that just entered
        Make sure actions here are quick
        
        This is just like stateEntered, perform only exit/actions here
        """

        Log.d(f'State {state} exited on event {event}')
        if state == 0:
            # exit actions for state 0
            pass
        # etc.
    
    def stateEvent(self, state, event)->bool:
        """
        stateEvent - handler for performing actions for a specific event
        without leaving the current state. 
        Note that transitions take precedence over state events, so if you
        have a transition as well as an in-state action for the same event,
        the in-state action will never be called.

        This handler must return True if the event was processed, otherwise
        must return False.
        """
        
        # Recommend using the debug statement below ONLY if necessary - may
        # generate a lot of useless debug information.
        # Log.d(f'State {state} received event {event}')
        
        # Handle internal events here - if you need to do something
        if state == 0 and event == 'button1_press':
            # do something for button1 press in state 0 wihout transitioning
            self._timer.cancel()
            return True
        
        # Note the return False if notne of the conditions are met
        return False

    def stateDo(self, state):
        """
        stateDo - the method that handles the do/actions for each state
        """
        
        # Now if you want to do different things for each state that has do actions
        if state == 0:
            # State 0 do/actions
            pass
        elif state == 1:
            pass
        elif state == 2:

            # Remember you do not need to create a loop - the model takes care of that
            # For example, if you want a state to flash an LED, just turn it on and off
            # once, and the model will repeat it as long as you are in that state.
            self.led.on()
            time.sleep(0.1)
            self.led.off()
            time.sleep(0.1)

    def run(self):
        """
        Create a run() method - you can call it anything you want really, but
        this is what you will need to call from main.py or someplace to start
        the state model.
        """
        
        # The run method should simply do any initializations (if needed)
        # and then call the model's run method.
        # You can send a delay as a parameter if you want something other
        # than the default 0.1s. e.g.,  self._model.run(0.25)
        self._model.run()

    def stop(self):
        # The stop method should simply do any cleanup as needed
        # and then call the model's stop method.
        # This removes the button's handlers but will need to see
        # if the IRQ handlers should also be removed
        self._model.stop()
        

# Test your model. Note that this only runs the template class above
# If you are using a separate main.py or other control script,
# you will run your model from there.
if __name__ == '__main__':
    p = MyController()
    try:
        p.run()
    except KeyboardInterrupt:
        p.stop()    
