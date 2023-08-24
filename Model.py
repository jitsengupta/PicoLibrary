"""
# Model.py
# A State model implementation
# Author: Arijit Sengupta
"""
import time

NO_EVENT = 0
BTN1_PRESS = 1
BTN1_RELEASE = 2
BTN2_PRESS = 3
BTN2_RELEASE = 4
BTN3_PRESS = 5
BTN3_RELEASE = 6
BTN4_PRESS = 7
BTN4_RELEASE = 8
TIMEOUT = 9

NUMEVENTS = 10
EVENTNAMES = ["NO_EVENT", "BTN1_PRESS", "BTN1_RELEASE", "BTN2_PRESS","BTN2_RELEASE",
                "BTN3_PRESS", "BTN3_RELEASE", "BTN4_PRESS","BTN4_RELEASE",
                "TIMEOUT"]

class Model:
    """
    A really simple implementation of a generic state model
    Keeps track of a number of states by sending the total number
    of states to the constructor. State numbers always start from 0
    which is the start state.

    Also takes a handler which is just a reference to a class that has
    three responder methods. The responder methods for stateEntered and
    stateLeft receives the state that was entered or left,
    with the event code that caused it. stateDo only receives the current
    state.
    
        stateEntered(state, event)
        stateLeft(state, event)
        stateDo(state)

    Currently there are 10 hardcoded events that are supported.
    
    * BTN1_PRESS/RELEASE through BTN4_PRESS/RELEASE are for button presses
    and releases - in the order they are created.
    * TIMEOUT is the event for a software or hardware timer. Only one
    timer can be active at a time
    * NO_EVENT is for non-event-related transitions. So if a state performs 
    the entry actions and do actions and then immediately goes to the next state, 
    NO_EVENT can be used. 

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

    def addTransition(self, fromState, events, toState):
        """
        Once the model is created, you must add all the transitions
        for known events. The model can handle events for button presses
        up to 4 buttons are supported. And it can also handle a timeout
        event created by a software or hardware timer. See documentation
        of the Counters classes to see how to use them.
        """
        for event in events:
            self._transitions[fromState][event] = toState
    
    def start(self):
        """ start the state model - always starts at state 0 as the start state """
        
        self._curState = 0
        self._running = True
        self._handler.stateEntered(self._curState, NO_EVENT)  # start the state model

    def stop(self):
        """
        stop the state model - this will call the handler one last time with
        what state was stopped at, and then set the running flag to false.
        """
    
        if self._running:
            self._handler.stateLeft(self._curState, NO_EVENT)
        self._running = False
        self._curState = -1

    def gotoState(self, newState, event=NO_EVENT):
        """
        force the state model to go to a new state. This may be necessary to call
        in response to an event that is not automatically handled by the Model class.
        This will correctly call the stateLeft and stateEntered handlers
        """
        
        if (newState < self._numstates):
            if self._debug:
                print(f"Going from State {self._curState} to State {newState}")
            self._handler.stateLeft(self._curState, event)
            self._curState = newState
            self._handler.stateEntered(self._curState, event)

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
                    if event != NO_EVENT:
                        print(f"Ignoring event {EVENTNAMES[event]}")
            else:
                if self._debug:
                    print(f"Processing event {EVENTNAMES[event]}")
                self.gotoState(self._transitions[self._curState][event], event)

    def run(self, delay=0.1):        
        # Start the model first
        self.start()
        # Then it should do a continous loop while the model runs
        while self._running:
            # Inside, you can use if statements do handle various do/actions
            # that you need to perform for each state
            # Do not perform entry and exit actions here - those are separate
                        
            self._handler.stateDo(self._curState)
            self.processEvent(NO_EVENT)
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
