from enum import Enum, auto
import time
import threading
import msvcrt
import tempfile
from sys import exit

from watchdog.observers import Observer
from xLPyBasics.PathAPI import (
    Path,
    PathHandler
)
from xLPyBasics.ConsoleAPI import LoggerRegistry

import EventWatcher
import Core as Core
from Sounds import (
    init as init_sounds,
    ROBLOX_TEMP_SOUNDS_DIR,
)
from Core import (
    init as init_core,
    LogChannel
)
from ModeManager import init as init_modes
import SoundInterface

try: import Copier
except: import Mock_Copier as Copier

# run modes
class Mode(Enum):
    Identifier = auto()
    Gains = auto()
def _startIdentifier() -> None:
    # create observer, and shedule it to watch for changes
    observer = Observer()
    observer.schedule(EventWatcher.EventIdentifier(), ROBLOX_TEMP_SOUNDS_DIR.get())
    LoggerRegistry.log_at(LogChannel.Log, "starting identifier thread")
    observer.start()

    # sleep, waiting for changes
    try:
        while True:
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()
        LoggerRegistry.log_at(LogChannel.Log, "stopped identifier thread")

def launch(mode: Mode) -> None:
    # lock the program from running multiple times
    lock = PathHandler(Path("pressure_voicelines.lock", prepension=tempfile.gettempdir()))
    try:
        lock_file = lock.open("w")
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
    except (OSError): # close if already open
        print("closed early")
        exit(0)

    # initialize
    init_core()
    init_sounds()
    init_modes()
    
    # switch over possible modes
    match mode:
        case Mode.Identifier:
            # start identifier
            thread = threading.Thread(target=_startIdentifier, daemon=True)
            thread.start()

            # show audio slider (blocks thread)
            SoundInterface.launch()

            # stop 
            thread.join()

        case Mode.Gains: 
            Copier.apply_gains()

        case _: 
            raise ValueError("mode was not a valid mode")
        
    