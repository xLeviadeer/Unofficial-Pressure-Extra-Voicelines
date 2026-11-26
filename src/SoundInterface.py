from typing import Callable, Self
import threading
import time
import pygame as pg
import tkinter as tk
from sys import exit
import random

import Core as Core
from Core import (
    LogChannel
)
import Sounds
from Sounds import (
    ROBLOX_TEMP_SOUNDS_DIR,
    SoundOptions, VoiceOptions, CategoryOptions
)

from xLPyBasics import Sentinels as df
from xLPyBasics.Singletons import Singleton
from xLPyBasics.PathAPI import (
    Path,
    PathHandler
)
from xLPyBasics.ConsoleAPI import LoggerRegistry

POPUP_WINDOW_WIDTH = 400 # pixels
BACKGROUND_COLOR = "#d9d9d9" # rgb
MAIN_MARGINS = 5 # pixels 
ICON_PATH = Path("assets", "icon.ico", prepension=Path.get_meipass(Path.cwd()))

class SoundInterface(Singleton):
    def __init__(self: Self) -> None:
        self.root_window: tk.Tk = None

        # mirror values
        self.do_rickety_mode: bool = False
        self.gif_button: tk.Button = None

    # show popup
    def show_popup(self: Self, title: str, body: str, buttonText: str, confirmCommand: Callable) -> None:
        global POPUP_WINDOW_WIDTH
        MARGIN_SIZE = 10

        # create popup warning
        popup_warning = tk.Toplevel(self.root_window, background=BACKGROUND_COLOR)
        popup_warning.title(title)
        popup_warning.iconbitmap(ICON_PATH.get())
        popup_warning.resizable(False, False)
        popup_warning.attributes("-topmost", True)

        # add label warning text
        tk.Label(
            popup_warning,
            text=body,
            wraplength=POPUP_WINDOW_WIDTH - (MARGIN_SIZE * 2),
            justify="left",
            background=BACKGROUND_COLOR
        ).pack(pady=MARGIN_SIZE, padx=MARGIN_SIZE)

        # confirmation button
        tk.Button(
            popup_warning,
            text=buttonText,
            command=lambda: confirmCommand(popup_warning)
        ).pack(pady=MARGIN_SIZE, padx=MARGIN_SIZE, anchor="e")

        # popup window settings and sizing
        popup_warning.update_idletasks()
        popup_warning.geometry(f"{POPUP_WINDOW_WIDTH}x{popup_warning.winfo_height()}")
        popup_warning.grab_set() # prevent interaction with other windows
        self.root_window.wait_window(popup_warning) # make it a popup

    # show window
    def show_window(self: Self) -> None:
        # create root tkinter window
        self.root_window = tk.Tk()
        self.root_window.attributes("-topmost", True)
        self.root_window.title("Pressure Extra Voicelines Audio Level")
        self.root_window.iconbitmap(ICON_PATH.get())

        # main grid
        outer_grid = tk.Frame(self.root_window, background=BACKGROUND_COLOR)
        outer_grid.rowconfigure(0, weight=1)
        outer_grid.rowconfigure(1, minsize=3)
        outer_grid.rowconfigure(2, weight=1)
        outer_grid.columnconfigure(0, weight=1)
        outer_grid.pack(padx=0, pady=0, fill="both", expand=True)

        # splitter color
        splitter = tk.Frame(outer_grid) # default background
        splitter.grid(row=1, column=0, sticky="nsew")

        # upper grid
        upper_grid = tk.Frame(outer_grid, background=BACKGROUND_COLOR)
        upper_grid.rowconfigure(0, weight=1)
        upper_grid.rowconfigure(1, minsize=20)
        upper_grid.columnconfigure(0, weight=1)
        upper_grid.columnconfigure(1, minsize=100)
        upper_grid.grid(row=0, column=0, sticky="nsew", pady=(MAIN_MARGINS, 0), padx=MAIN_MARGINS)

        # lower grid
        lower_grid = tk.Frame(outer_grid, background=BACKGROUND_COLOR)
        lower_grid.rowconfigure(0, weight=1)
        lower_grid.columnconfigure(0, weight=1)
        lower_grid.columnconfigure(1, weight=1)
        lower_grid.columnconfigure(2, weight=1)
        lower_grid.grid(row=2, column=0, sticky="nsew", pady=(0, MAIN_MARGINS), padx=MAIN_MARGINS)

        # add sound slider
        volume_slider = tk.Scale(
            upper_grid, 
            from_=0,
            to=100,
            orient="horizontal",
            label="Volume",
            command=lambda vol: Sounds.set_volume(vol, True),
            background=BACKGROUND_COLOR,
            highlightthickness=0 # gets rid of a weird white border
        )
        volume_slider.grid(row=0, rowspan=2, column=0, sticky="nsew", padx=MAIN_MARGINS, pady=MAIN_MARGINS)
        volume_slider.set(100)

        # manual wipe button
        def on_click_wipe_button():
            def on_click_understand(popup_warning: tk.Toplevel):
                # delete temp sounds
                Sounds.delete_temp_sounds()
                LoggerRegistry.log_at(LogChannel.Log, "wiped temp roblox files")

                # close window
                popup_warning.destroy()
            self.show_popup(
                "Warning for manually wiping",
                "Manually wiping will clear the cache that this program relies on and fix some cache-based errors. However it will ¡not¡ fix ⌄. For these errors, a program restart is required.\n"
                + "\t• whether the program knows if the player is in the game ╎ the program will not function unless you open it before starting a game\n"
                + "\t• recover from crashed subsystems such as occurance detection, random voice generation, sound effect playing\n",
                "I understand",
                on_click_understand
            )
        wipe_button = tk.Button(
            upper_grid,
            text="Force Wipe",
            command=on_click_wipe_button,
        )
        wipe_button.grid(row=1, column=1, sticky="nsew", padx=MAIN_MARGINS, pady=MAIN_MARGINS)

        # rickety splickety mode
        _rickety_mode_enabled = tk.BooleanVar(value=self.do_rickety_mode)
        def _sync_rickety_mode(*args):
            self.do_rickety_mode = _rickety_mode_enabled.get()
            LoggerRegistry.log_at(LogChannel.SettingChange, f"set the new value for rickety splickety mode to {self.do_rickety_mode}")
        _rickety_mode_enabled.trace_add("write", _sync_rickety_mode)
        rickety_button = tk.Checkbutton(
            lower_grid, 
            text="Rickety Splickety Mode",
            variable=_rickety_mode_enabled,
            background=BACKGROUND_COLOR
        )
        rickety_button.grid(row=0, column=0, sticky="w")

        # gif mode
        _gif_mode_enabled = tk.BooleanVar(value=Sounds.voices[VoiceOptions.GIF].is_enabled)
        def _sync_gif_mode(*args):
            newValue = _gif_mode_enabled.get()
            LoggerRegistry.log_at(LogChannel.SettingChange, f"set the new value for {VoiceOptions.GIF.name} to {newValue}")
            Sounds.voices[VoiceOptions.GIF].is_enabled = newValue
            if (newValue == True): 
                Sounds.play_sound(CategoryOptions.Enter, VoiceOptions.GIF)
        _gif_mode_enabled.trace_add("write", _sync_gif_mode)
        self.gif_button = tk.Checkbutton(
            lower_grid, 
            text="Green Friend Mode",
            variable=_gif_mode_enabled,
            background=BACKGROUND_COLOR
        )
        self.gif_button.grid(row=0, column=1, sticky="w")

        # shutting down noise
        def on_close():
            # channel: pg.mixer.Channel = Sounds.play_sound(SoundOptions.ShuttingDown) # play shutting down sound
            # while channel.get_busy(): time.sleep(0.5) # wait for sound to finish
            Core.deinit() # de init
            self.root_window.destroy() # kill window
            exit() # exit everything
        self.root_window.protocol("WM_DELETE_WINDOW", on_close)

        # get ready to show so geometry is correct
        self.root_window.update_idletasks()

        # sizing
        height = self.root_window.winfo_height()
        self.root_window.maxsize(1000, height)
        self.root_window.minsize(500, height)
        self.root_window.geometry(f"500x{height}")
        self.root_window.resizable(True, False)

        # start root window
        self.root_window.mainloop()

# timing consts
_DELETE_DETECTION_TIME: int = 30 # 0:30
_RICKETY_SECONDS_MIN: int = int(7 * 60) # 7:00
_RICKETY_SECONDS_MAX: int = int(20 * 60) # 20:00
_RANDOM_TALKING_SECONDS_MIN: int = 90 # 1:30
_RANDOM_TALKING_SECONDS_MAX: int = 150 # 2:30

# single only handler interface
handler: SoundInterface|df.Type.Unset = df.Value.Unset

# enabled by enter game
# disabled by lobby or final boss battle
currently_in_game: bool = False

_was_inited: bool = False
def init() -> None:
    global handler
    global _was_inited

    # don't init twice
    if _was_inited: raise RuntimeError("cannot initialize twice")
    _was_inited = True

    # set handler & init runners
        # runners get ignored if they are disabled but always run
    handler = SoundInterface()
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
        global handler
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
            handler.gif_button.config(state="active")
            currently_in_game = False
            LoggerRegistry.log_at(LogChannel.Log, "game is now stopped: exit detected")
    timer = _timer(_DELETE_DETECTION_TIME, delete_files_check_for_exit)
    threading.Thread(target=timer, daemon=True).start()
    LoggerRegistry.log_at(LogChannel.Log, "ran game active thread")

# don't ever run this twice
def _rickety_splickety_mode() -> None:
    def play_rabba_sound() -> None:
        global handler
        global currently_in_game

        # play sound effect
        if (
            (handler.do_rickety_mode) # rickety splickety mode enabled
            and (currently_in_game) # currently in the game
        ):
            Sounds.play_sound(SoundOptions.Rabba)
            channel = Sounds.playing_sounds[SoundOptions.Rabba]
            while channel.get_busy(): # wait for sound to finish
                # stop if unchecked mid playback
                if (
                    (not handler.do_rickety_mode)
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
            (Sounds.voices[VoiceOptions.GIF].is_enabled) # rickety splickety mode enabled
            and (currently_in_game) # currently in the game
        ):
            gif_key = Sounds.play_sound(CategoryOptions.Random, VoiceOptions.GIF)
            channel = Sounds.playing_sounds[gif_key]
            while channel.get_busy(): # wait for sound to finish
                # stop if unchecked mid playback
                if (
                    (not handler.do_rickety_mode)
                    or (not currently_in_game)
                ): channel.stop()
                time.sleep(0.2) # wait some time
    timer = _timer((_RANDOM_TALKING_SECONDS_MIN, _RANDOM_TALKING_SECONDS_MAX), talk_something)
    threading.Thread(target=timer, daemon=True).start()
    LoggerRegistry.log_at(LogChannel.Log, "ran GIF thread")

# don't ever run this twice
