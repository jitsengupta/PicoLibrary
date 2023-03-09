# A State model implementation

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
class Model:
    def __init__(self, numstates, handler, debug=False): 
        self._numstates = numstates
        self._running = False
        self._transitions = []
        for i in range(0, numstates):
            self._transitions.append([None]*NUMEVENTS)
        self._curState = -1
        self._handler = handler
        self._debug = debug

    def start(self):
        self._curState = 0
        self._running = True
        self._handler.stateEntered(self._curState)  # start the state model

    def stop(self):
        if self._running:
            self._handler.stateLeft(self._curState)
        self._running = False
        self._curState = -1

    def gotoState(self, newState):
        if (newState < self._numstates):
            if self._debug:
                print(f"Going from State {self._curState} to State {newState}")
            self._handler.stateLeft(self._curState)
            self._curState = newState
            self._handler.stateEntered(self._curState)

    def addTransition(self, fromState, event, toState):
        self._transitions[fromState][event] = toState

    def processEvent(self, event):
        if (event < NUMEVENTS):
            newstate = self._transitions[self._curState][event]
            if newstate is None:
                if self._debug:
                    print(f"Ignoring event {EVENTNAMES[event]}")
            else:
                if self._debug:
                    print(f"Processing event {EVENTNAMES[event]}")
                self.gotoState(self._transitions[self._curState][event])
            

