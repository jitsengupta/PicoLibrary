"""
# Model.py
# A State model implementation
# Author: Arijit Sengupta
"""
import time


BTN1_PRESS = 0
BTN1_RELEASE = 1
BTN2_PRESS = 2
BTN2_RELEASE = 3
BTN3_PRESS = 4
BTN3_RELEASE = 5
BTN4_PRESS = 6
BTN4_RELEASE = 7
TIMEOUT = 8

NUMEVENTS = 9
EVENTNAMES = ["BTN1_PRESS", "BTN1_RELEASE", "BTN2_PRESS","BTN2_RELEASE",
                "BTN3_PRESS", "BTN3_RELEASE", "BTN4_PRESS","BTN4_RELEASE",
                "TIMEOUT"]

class Model:
    """
    A really simple implementation of a generic state model
    Keeps track of a number of states by sending the total number
    of states to the constructor. State numbers always start from 0
    which is the start state.

    Also takes a handler which is just a reference to a class that has
    two responder methods:
        stateEntered(state)
        stateLeft(state)

    The calling class or the handler must override stateEntered and
    stateLeft to perform actions as per the state model

    After creating the state, call addTransition to determine
    how the model transitions from one state to the next.

    As events start coming in, call processEvent on the event to
    have the state model transition as per the transition matrix.
    """
    
    def __init__(self, numstates, handler, debug=False):
        """
        The model constructor - needs 2 things minimum:
        Parameters
        ----------
        numstates - the number of states in the State model (includes the start and end states)
        handler - the handler class that should implement the model actions stateEntered and stateLeft
         - stateEntered will receive as parameter which state the model has entered - this should
            allow the handler to execute entry actions
         - stateLeft will receive as parameter which state the model left - this will allow the handler
            to execute the exit actions.
        all continuous in-state actions must be implemented in the handler in a execute loop.
        
        debug will print things to the screen like active state, transitions, events, etc.
        """
        
        self._numstates = numstates
        self._running = False
        self._transitions = []
        for i in range(0, numstates):
            self._transitions.append([None]*NUMEVENTS)
        self._curState = -1
        self._handler = handler
        self._debug = debug
        self._buttons = []
        self._timer = None

    def addTransition(self, fromState, event, toState):
        """
        Once the model is created, you must add all the transitions
        for known events. The model can handle events for button presses
        up to 4 buttons are supported. And it can also handle a timeout
        event created by a software or hardware timer. See documentation
        of the Counters classes to see how to use them.
        """
        
        self._transitions[fromState][event] = toState
    
    def start(self):
        """ start the state model - always starts at state 0 as the start state """
        
        self._curState = 0
        self._running = True
        self._handler.stateEntered(self._curState)  # start the state model

    def stop(self):
        """
        stop the state model - this will call the handler one last time with
        what state was stopped at, and then set the running flag to false.
        """
    
        if self._running:
            self._handler.stateLeft(self._curState)
        self._running = False
        self._curState = -1

    def gotoState(self, newState):
        """
        force the state model to go to a new state. This may be necessary to call
        in response to an event that is not automatically handled by the Model class.
        This will correctly call the stateLeft and stateEntered handlers
        """
        
        if (newState < self._numstates):
            if self._debug:
                print(f"Going from State {self._curState} to State {newState}")
            self._handler.stateLeft(self._curState)
            self._curState = newState
            self._handler.stateEntered(self._curState)

    def processEvent(self, event):
        """
        Get the model to process an event. The event should be one of the events defined
        at the top of the model class. Currently 4 button press and release events, and
        a timeout event is supported. Handlers for the buttons and the timers should be
        incorporated in the main class, and processevent should be called when these handlers
        are triggered.
        
        I may try to improve this design a bit in the future, but for now this is how it is
        built.
        """
        
        if (event < NUMEVENTS):
            newstate = self._transitions[self._curState][event]
            if newstate is None:
                if self._debug:
                    print(f"Ignoring event {EVENTNAMES[event]}")
            else:
                if self._debug:
                    print(f"Processing event {EVENTNAMES[event]}")
                self.gotoState(self._transitions[self._curState][event])

    def run(self, delay=0.1):        
        # Start the model first
        self.start()
        # Then it should do a continous loop while the model runs
        while self._running:
            # Inside, you can use if statements do handle various do/actions
            # that you need to perform for each state
            # Do not perform entry and exit actions here - those are separate
                        
            self._handler.stateDo(self._curState)
            
            # Ping the timer if it is a software timer
            if self._timer is not None and type(self._timer).__name__ == 'SoftwareTimer':
                self._timer.check()
            
            # I suggest putting in a short wait so you are not overloading the poor Pico
            if delay > 0:
                time.sleep(delay)

    def addButton(self, btn):
        if len(self._buttons) < 4:
            btn.setHandler(self)
            self._buttons.append(btn)
        else:
            raise ValueError('Currently we only support up to 4 buttons')

    def buttonPressed(self, name):
        """ 
        The internal button handler - now Model can take care of buttons
        that have been added using the addButton method.
        """

        for i in range(0,len(self._buttons)):
            if name == self._buttons[i]._name:
                if i == 0:
                    self.processEvent(BTN1_PRESS)
                elif i == 1:
                    self.processEvent(BTN2_PRESS)
                elif i == 2:
                    self.processEvent(BTN3_PRESS)
                elif i == 3:
                    self.processEvent(BTN4_PRESS)

    """
    Same thing with Button release, if you want to handle release events
    As well as press or just want to do release events only.
    """
    def buttonReleased(self, name):
        for i in range(0,len(self._buttons)):
            if name == self._buttons[i]._name:
                if i == 0:
                    self.processEvent(BTN1_RELEASE)
                elif i == 1:
                    self.processEvent(BTN2_RELEASE)
                elif i == 2:
                    self.processEvent(BTN3_RELEASE)
                elif i == 3:
                    self.processEvent(BTN4_RELEASE)

    def addTimer(self, timer):
        self._timer = timer
        self._timer.setHandler(self)

    """
    If you are using a timer, handle the timeout callback
    My model can use timeout events for transitions, so simply
    send the event to the model and it will take care of
    the rest.
    """
    def timeout(self):
        self.processEvent(TIMEOUT)
