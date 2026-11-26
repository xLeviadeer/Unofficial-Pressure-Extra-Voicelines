from typing import (
    Self,
    Callable
)
from enum import Enum, auto
import time
import random
import threading

from xLPyBasics import Sentinels as df
from xLPyBasics.PathAPI import (
    PathHandler
)
from xLPyBasics.ConsoleAPI import LoggerRegistry
from xLPyBasics.StructuresAPI import Event

from Core import (
    LogChannel
)
import Sounds
from Sounds import (
    ROBLOX_TEMP_SOUNDS_DIR,
    SoundOptions, VoiceOptions, CategoryOptions
)

_DELETE_DETECTION_TIME: int = 30 # 0:30
_RICKETY_SECONDS_MIN: int = int(7 * 60) # 7:00
_RICKETY_SECONDS_MAX: int = int(20 * 60) # 20:00
_RANDOM_TALKING_SECONDS_MIN: int = 90 # 1:30
_RANDOM_TALKING_SECONDS_MAX: int = 150 # 2:30

# enabled by enter game
# disabled by lobby or final boss battle
currently_in_game: bool = False

class Mode:
    __name: str
    @property
    def name(self: Self) -> str: return self.__name

    __is_enabled: bool
    @property
    def is_enabled(self: Self) -> bool: return self.__is_enabled
    @is_enabled.setter
    def is_enabled(self: Self, val: bool) -> None: 
        self.__is_enabled = val
        self.on_changed.emit(val)

    __on_changed: Event[bool]
    @property
    def on_changed(self: Self) -> Event[bool]: return self.__on_changed

    __linked_voice: VoiceOptions|df.Type.Empty
    @property
    def linked_voice(self: Self) -> VoiceOptions|df.Type.Empty: return self.__linked_voice

    def __init__(
        self: Self,
        name: str,
        is_enabled: bool,
        linked_voice: VoiceOptions|df.Type.Empty = df.Value.Empty
    ) -> None:
        self.__name = name
        self.__is_enabled = is_enabled
        self.__on_changed = Event[bool]()
        self.__linked_voice = linked_voice
        
class ModeOptions(Enum): 
    Rickety = Mode("Ricket Splickety", False)
    GIF = Mode("Green Friend", False, VoiceOptions.GIF)

_was_inited: bool = False
def init() -> None:
    global _was_inited

    # don't init twice
    if _was_inited: raise RuntimeError("cannot initialize twice")
    _was_inited = True

    # run threads
    _game_active_loop()
    _rickety_splickety_mode()
    _GIF_mode()

def _timer(
    sleep_time: int|tuple[int, int],
    on_complete: Callable[[], None]
) -> Callable[[], None]:
    """creates a timer function which calls the on_complete method when it completes a cycle

    Args:
        time (int | tuple[int, int]): a single (definite) time (seconds) that it takes for a cycle to complete ∨ a bound of time (seconds) which will be randomly selected between for a cycle to complete
        on_complete (Callable[[], None]): the method to invoke upon completion

    Returns:
        Callable[[], None]: an async method to be invoked (via asyncio)
    """
    def timer_func() -> None:
        nonlocal sleep_time

        # run until thread completion
        while True:
            # wait for time
            curr_time = (
                random.randint(sleep_time[0], sleep_time[1])
                if isinstance(sleep_time, tuple)
                else sleep_time
            )
            time.sleep(curr_time)

            # run completion method
            on_complete()
    return timer_func

# don't ever run this twice
def _game_active_loop():
    def delete_files_check_for_exit() -> None:
        global currently_in_game

        # if there are no files to delete to start with and the game isn't running, then don't exit
        dir_conts = PathHandler(ROBLOX_TEMP_SOUNDS_DIR).read_dir()
        if (
            (len(dir_conts) == 0)
            and (currently_in_game == False)
        ): return

        # for every roblox sound
        for file in dir_conts:
            # try to delete it
            try: file.remove()
            except (PermissionError, OSError): 
                # at least one file was in use, try again next cycle
                LoggerRegistry.log_at(LogChannel.Log, "still in game")
                break
        else: # didn't break
            # game must not be running
            Sounds.play_sound(SoundOptions.Exit)
            currently_in_game = False
            LoggerRegistry.log_at(LogChannel.Log, "game is now stopped: exit detected")
    timer = _timer(_DELETE_DETECTION_TIME, delete_files_check_for_exit)
    threading.Thread(target=timer, daemon=True).start()
    LoggerRegistry.log_at(LogChannel.Log, "ran game active thread")

# don't ever run this twice
def _rickety_splickety_mode() -> None:
    def play_rabba_sound() -> None:
        global currently_in_game

        # play sound effect
        if (
            (ModeOptions.Rickety.value.is_enabled) # rickety splickety mode enabled
            and (currently_in_game) # currently in the game
        ):
            Sounds.play_sound(SoundOptions.Rabba)
            channel = Sounds.playing_sounds[SoundOptions.Rabba]
            while channel.get_busy(): # wait for sound to finish
                # stop if unchecked mid playback
                if (
                    (not ModeOptions.Rickety.value.is_enabled)
                    or (not currently_in_game)
                ): channel.stop()
                time.sleep(0.2) # wait some time
    timer = _timer((_RICKETY_SECONDS_MIN, _RICKETY_SECONDS_MAX), play_rabba_sound)
    threading.Thread(target=timer, daemon=True).start()
    LoggerRegistry.log_at(LogChannel.Log, "ran rickety splickety thread")

# don't ever run this twice
def _GIF_mode() -> None:
    def talk_something() -> None:
        global currently_in_game

        # play sound effect
        if (
            (ModeOptions.GIF.value.is_enabled) # rickety splickety mode enabled
            and (currently_in_game) # currently in the game
        ):
            gif_key = Sounds.play_sound(CategoryOptions.Random, VoiceOptions.GIF)
            channel = Sounds.playing_sounds[gif_key]
            while channel.get_busy(): # wait for sound to finish
                # stop if unchecked mid playback
                if (
                    (not ModeOptions.GIF.value.is_enabled)
                    or (not currently_in_game)
                ): channel.stop()
                time.sleep(0.2) # wait some time
    timer = _timer((_RANDOM_TALKING_SECONDS_MIN, _RANDOM_TALKING_SECONDS_MAX), talk_something)
    threading.Thread(target=timer, daemon=True).start()
    LoggerRegistry.log_at(LogChannel.Log, "ran GIF thread")
