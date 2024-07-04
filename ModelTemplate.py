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
from Button import *


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

class MyControllerTemplate:

    def __init__(self):
        
        # Instantiate whatever classes from your own model that you need to control
        # Handlers can now be set to None - we will add them to the model and it will
        # do the handling
        
        # Instantiate a Model. Needs to have the number of states, self as the handler
        # You can also say debug=True to see some of the transitions on the screen
        # Here is a sample for a model with 4 states
        self._model = StateModel(2, self, debug=True)
        
        # Instantiate any Buttons that you want to process events from and add
        # them to the model
        self._button = Button(20, "button1", handler=None)        
        self._model.addButton(self._button)
        
        # add other buttons if needed. Note that button names must be distinct
        # for all buttons. Events will come back with [buttonname]_press and
        # [buttonname]_release
        
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
        self._model.addTransition(1, ["timer1_timout"], 0)
        # etc.
    
    """
    stateEntered - is the handler for performing entry/actions
    You get the state number of the state that just entered
    Make sure actions here are quick
    """
    def stateEntered(self, state, event):
        # Again if statements to do whatever entry/actions you need
        Log.d(f'State {state} entered on event {event}')
        if state == 0:
            # entry actions for state 0
            pass
        
        elif state == 1:
            # entry actions for state 1
            self._timer.start(5)
        
            
    """
    stateLeft - is the handler for performing exit/actions
    You get the state number of the state that just entered
    Make sure actions here are quick
    
    This is just like stateEntered, perform only exit/actions here
    """

    def stateLeft(self, state, event):
        Log.d(f'State {state} exited on event {event}')
        if state == 0:
            # exit actions for state 0
            pass
        # etc.
    
    """
    stateDo - the method that handles the do/actions for each state
    """
    def stateDo(self, state):
        # Now if you want to do different things for each state you can do it:
        if state == 0:
            # State 0 do/actions
            pass
        elif state == 1:
            # State1 do/actions
            # You can check your sensors here and process events manually if custom events
            # are needed (these must be previously added using addCustomEvent()
            # For example, if you want to go from state 1 to state 2 when the motion sensor
            # is tripped you can do something like this
            # In __init__ - you should have done self._model.addCustomEvent("motion")
            # Here, you check the conditions that should check for this condition
            # Then ask the model to handle the event
            # if self.motionsensor.tripped():
            # 	self._model.processEvent("motion")
            pass

    """
    Create a run() method - you can call it anything you want really, but
    this is what you will need to call from main.py or someplace to start
    the state model.
    """
    def run(self):
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
    p = MyControllerTemplate()
    try:
        p.run()
    except KeyboardInterrupt:
        p.stop()    
