from typing import (
    Self,
    TextIO
)
from enum import Enum, auto

import pygame as pg
from xLPyBasics import Sentinels as df
from xLPyBasics.PathAPI import (
    Path,
    PathHandler
)
from xLPyBasics.ConsoleAPI import (
    LoggerRegistry,
    DefChl,
    ChannelSettings, ChannelGroupSettings
)
from xLPyBasics.xQWERTILE import xstr

# ———DATA———

PROGRAM_VERSION: str = "2.0.0"

class LogChannel(Enum):
    GPEV = auto()
    Found = auto()
    Log = auto()
    SettingChange = auto()
    Warning = auto()

_logging_file: TextIO|df.Type.Unset = df.Value.Unset

# ———METHODS———

_was_inited: bool = False
def init() -> None:
    global _was_inited
    global _logging_file

    # don't init twice
    if _was_inited: raise RuntimeError("cannot initialize twice")
    _was_inited = True

    # ║ Initialize Logging

    # logger file open
    logging_handler = PathHandler(Path("logs", "log", extension="txt", prepension=Path.get_meipass(Path.cwd())))
    logging_handler.write("")
    _logging_file = logging_handler.open("w", encoding="utf-8")

    # logger subscription
    def append_to_log(emited: tuple[str, str, bool]) -> None:
        global _logging_file
        if emited[2]: _logging_file.write(xstr(f"{emited[1]}ใn").parsed)
    LoggerRegistry.at(DefChl.Log).on_log.subscribe(append_to_log)

    # logger channels
    LoggerRegistry.add(ChannelGroupSettings(LogChannel.GPEV, "GPEV", separator=" ", do_sectioning=False))
    LoggerRegistry.at(LogChannel.GPEV).add(ChannelSettings(LogChannel.Found, "!"))
    LoggerRegistry.at(LogChannel.GPEV).add(ChannelSettings(LogChannel.Log, "-"))
    LoggerRegistry.at(LogChannel.GPEV).add(ChannelSettings(LogChannel.SettingChange, "+"))
    LoggerRegistry.at(LogChannel.GPEV).add(ChannelSettings(LogChannel.Warning, "⚠"))

    # log version
    LoggerRegistry.log_at(DefChl.Log, f"program version: {PROGRAM_VERSION}")

    # ║ PyGame
    pg.mixer.init()

def deinit() -> None:
    # ║ De-Initiliaze Logging

    # close logger file
    global _logging_file
    if (not _logging_file.closed): _logging_file.close()