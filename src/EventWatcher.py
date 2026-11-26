from typing import Self
import time
import threading
from sys import exit
import tkinter as tk

from watchdog.events import FileSystemEventHandler, FileSystemEvent
import numpy as np
import soundfile as sf
from xLPyBasics import Sentinels as df
from xLPyBasics.PathAPI import (
    Path,
    PathHandler
)
from xLPyBasics.ConsoleAPI import LoggerRegistry

import EventDefinitions as ev
import Core as Core
from Core import LogChannel
import Sounds
from Sounds import (
    SoundOptions
)
import SoundInterface

try: import Copier
except: import Mock_Copier as Copier

NUMBER_OF_DELETION_ATTEMPTS_BEFORE_ERROR = 5

# file copier event handler
class EventIdentifier(FileSystemEventHandler):
    # when any file is added to the directory, check it for an angler signature
    def on_created(self: Self, file_raw: FileSystemEvent) -> None:
        file = Path(file_raw.src_path)

        # check for any errors so a message can be shown if there is one
        try:
            if PathHandler(file).exists_dir: return # skip directories

            # open with sound file
            with sf.SoundFile(file.get()) as soundFile:
                # get the first few PCM frames
                first_frames = soundFile.read(frames=Sounds.IDENTIFICATION_DEPTH, dtype=Sounds.IDENTIFIER_TYPE)

                # check if the frames match any identifier
                for eventOption, eventId in ev.EVENT_SIGNATURES.items():
                    if (np.array_equal(
                        np.array(eventId[:Sounds.IDENTIFICATION_DEPTH]),
                        first_frames
                    )): 
                        # run found method
                        EventIdentifier.on_found(file, eventOption)
        except (Exception):
            Sounds.play_sound(SoundOptions.Error, do_stop=True) # play error sound
            Copier.dump_current() # create a dump
            Core.deinit() # close the logger so that all contents are written to it

            # create popup
            def exitAll(popup_window: tk.Toplevel):
                popup_window.destroy()
                exit(0)
                SoundInterface.handler.root_window.destroy()
            SoundInterface.handler.show_popup(
                "An error has occured",
                "ERROR: an error has occured and the program is no longer identifying occurances correctly, please take the following actions.\n"
                    + "Check to ensure you are on the most up-to-date version of the program\n"
                    + "1. send the developer the `log.txt` file generated in the `logs` folder.\n"
                        + "\t• you may need to close the program for it to appear ╎ do ¡not¡ start the program or the log file will be cleared"
                    + "2. close and re-open the program\n"
                    + "3. trigger a ⟨Manual Wipe⟩ to clear any sound fragments that may be left.\n"
                        + "\t• some occurances may no longer be properly detected even after completing the above successfully. Once the game you are playing has been left and re-joined, the program will work fully properly again.",
                " Okay ",
                exitAll 
            )
        
    # runs when an event is found
    @staticmethod
    def on_found(file: Path, event_option: ev.EventOptions) -> None:
        # alert message
        LoggerRegistry.log_at(LogChannel.Found, f"{event_option.value.name} \t({file.last})")

        # run event specifics
        if (ev.event_specifics(event_option) == True):
            LoggerRegistry.log_at(LogChannel.Log, "event continuing with \"normal\" processing")
            # "normal" processing where
                # a random sound is chosen from the category
                # or, the default sound is played

            # play sound
            if event_option.value.association is None: raise ValueError(f"association was None when trying to play sound for {event_option.name}")
            Sounds.play_sound(event_option.value.association) 

        # don't try to delete if
        if (
            (event_option.value.deletion_settings.deletion_interval == None) # event isn't error prone
            or (not event_option.value.associtation_is_categoric()) # or, event isn't categoric
        ): return

        # run delete file
        LoggerRegistry.log_at(LogChannel.Log, "will attempt to delete this file")
        timer = threading.Timer(
            event_option.value.deletion_settings.deletion_interval, # wait for the deletion iterval time before trying to delete
            function=EventIdentifier.delete_file,
            args=(file, event_option)
        )
        timer.daemon = True
        timer.start()

    # set a timer and delete the found file so it must be re-downloaded again
    @staticmethod
    def delete_file(path: Path, event_option: ev.EventOptions) -> None:
        file_name = path.last

        # try to delete until hit the failiure count
        attempt_count: int = 0
        while (
            df.Check.is_infinite(event_option.value.deletion_settings.deletion_count_max)
            or (attempt_count <= event_option.value.deletion_settings.deletion_count_max)
        ):
            # increment the attempt count
            if not df.Check.is_infinite(event_option.value.deletion_settings.deletion_count_max):
                attempt_count += 1

            # try to delete, let pass if unable
            try: 
                PathHandler(path).remove()
                break
            except FileNotFoundError: # file was otherwise deleted
                LoggerRegistry.log_at(LogChannel.Log, f"successfully deleted {file_name}")
                break
            except Exception: 
                if (attempt_count % NUMBER_OF_DELETION_ATTEMPTS_BEFORE_ERROR) == 0:
                    LoggerRegistry.log_at(LogChannel.Warning, f"continious errors when trying to delete {event_option.value.name} ({file_name})")
                time.sleep(event_option.value.deletion_settings.deletion_interval)
        else:
            # error alert
            LoggerRegistry.log_at(LogChannel.Warning, f"complete failiure when trying to delete {event_option.value.name} ({file_name}) ╎ as a result {event_option.value.name} may no longer be detectable")                
            Sounds.play_sound(ev.ERROR_SOUNDS[event_option])