
import time
from machine import Pin
from machine import WDT

from neotimer import *
from statemachine import *

DEBUG_MODE = True

BUTTON = Pin(2, Pin.IN)
LED_BUTTON = Pin(4, Pin.OUT)
SOM_RAIL = Pin(8, Pin.IN) 

SOM_SLEEP_WAKE = Pin(7, Pin.OUT, value=1)
SOM_SIGNAL = Pin(9, Pin.IN)
SOM_POWER_ENABLE = Pin(10, Pin.OUT, value=1)
EN_BUFFER = Pin(18, Pin.OUT, value=1)

LED_DEBUG = Pin(19, Pin.OUT)

state_machine = StateMachine()
debouncing_timer = Neotimer(1000)

preidle_timer = Neotimer(2000)
booting_timer = Neotimer(25000)
halting_timer = Neotimer(15000)

blinker = Neotimer(100)

heartbeat_on_time = Neotimer(50)
heartbeat_interval = Neotimer(1000)

button_duration = 0

wdt = WDT(timeout=5000)

class LED:

    def __init__(self, pin, inverted=False):
        self.pin = pin
        self.state = 0
        self.inverted = inverted

    def on(self):
        self.state = 1

        if self.inverted:
            self.pin.off()
        else:
            self.pin.on()

    def off(self):
        self.state = 0

        if self.inverted:
            self.pin.on()
        else:
            self.pin.off()

    def toggle(self):
        if self.state:
            self.off()
        else:
            self.on()

power_led = LED(LED_BUTTON)
debug_led = LED(LED_DEBUG, inverted=True)

def notify(string):
    if DEBUG_MODE:
        print("%.d %s" % (time.time(), string))

def is_pressed(pin):
    return not pin.value()

def blink_power_button():
    if blinker.repeat_execution():
        power_led.toggle()

def heartbeat():

    if heartbeat_interval.repeat_execution():
        # notify("IO %d 3v3 %d" % (SOM_SIGNAL.value(), SOM_RAIL.value()))
        heartbeat_on_time.start()
        wdt.feed()

    if heartbeat_on_time.waiting():
        debug_led.on()
    else:
        debug_led.off()

def suspending_a_logic():
    global button_duration

    if state_machine.execute_once:
        # Disable buffer, so that ESP continues to run when SOM shuts down
        EN_BUFFER.off()

        ## Disable UART.  This prevents MCU from halting when SOM does.
        ## Once this occurs, code cannot be updated again (as repl a)
        ## So, MCU must be reset via SOM for to update to occur
        Pin(20, Pin.OUT)

        notify("State : suspending A")

        # Send power off signal to SOM
        SOM_SLEEP_WAKE.off()

    blink_power_button()

    if debouncing_timer.debounce_signal(is_pressed(BUTTON)):
        notify("BUTTON %d" % button_duration)
        button_duration += 1

        ## Force shutdown has been triggered, go to hard power off
        if button_duration > 5:
            state_machine.force_transition_to(suspended)
            button_duration = 0

    if not is_pressed(BUTTON):
        button_duration = 0

    ## SOM has signaled back that it is doing the shutdown
    ## Go to state where we wait (via timer) for that to complete
    if SOM_SIGNAL.value() == False:
        state_machine.force_transition_to(suspending_b)
    
def suspending_b_logic():          
    if state_machine.execute_once:
        notify("State : suspending B")
        halting_timer.start()

    blink_power_button()

    if halting_timer.finished():
        state_machine.force_transition_to(suspended)

def suspended_logic():
    global button_duration

    if state_machine.execute_once:
        notify("State : suspended")
        power_led.off()

        # Turn off SOM regulators
        SOM_POWER_ENABLE.off()

        # Release assertion on power signal.  
        SOM_SLEEP_WAKE.on()

    if debouncing_timer.debounce_signal(is_pressed(BUTTON)):
        notify("BUTTON %d" % button_duration)
        button_duration += 1

        if button_duration > 1:
            state_machine.force_transition_to(starting_a)
            button_duration = 0

    if not is_pressed(BUTTON):
        button_duration = 0

def starting_a_logic():

    if state_machine.execute_once:
        notify("State : starting A")
        SOM_POWER_ENABLE.on()

    blink_power_button()

    if SOM_SIGNAL.value() and SOM_RAIL.value():
        state_machine.force_transition_to(starting_b)

def starting_b_logic():
    
    if state_machine.execute_once:
        notify("State : starting B")
        booting_timer.start()

    blink_power_button()

    if booting_timer.finished():
        state_machine.force_transition_to(idle)


def idle_logic():
    global button_duration

    if state_machine.execute_once:
        notify("State: idle")
        power_led.on()

        # Enable buffer, so that SOM can reboot MCU if needed
        EN_BUFFER.on()
    
    if debouncing_timer.debounce_signal(is_pressed(BUTTON)):
        notify("BUTTON %d" % button_duration)
        button_duration += 1

        if button_duration > 1:
            state_machine.force_transition_to(suspending_a)
            button_duration = 0
    
    if not is_pressed(BUTTON):
        button_duration = 0

    ## SOM has signaled back that it has initiated a shutdown 
    ## So, go to state where we disable the isolation buffer 
    if SOM_SIGNAL.value() == False:
        state_machine.force_transition_to(suspending_a)

## This state just waits a short period of time before going to idle
## This allows plenty of time for the SOM to assert the ENABLE pin
## prior to the MCU enabling the isolation buffer
def preidle_logic():
    if state_machine.execute_once:
        notify("State : preidle")
        preidle_timer.start()

    blink_power_button()

    if preidle_timer.finished():
        state_machine.force_transition_to(idle)


preidle = state_machine.add_state(preidle_logic)
idle = state_machine.add_state(idle_logic)
suspending_a = state_machine.add_state(suspending_a_logic)
suspending_b = state_machine.add_state(suspending_b_logic)
suspended = state_machine.add_state(suspended_logic)
starting_a = state_machine.add_state(starting_a_logic)
starting_b = state_machine.add_state(starting_b_logic)


while True:

    heartbeat()
    state_machine.run()