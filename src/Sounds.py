from typing import (
    Self,
    Iterator
)
from enum import Enum
import tempfile
import random
from dataclasses import dataclass
import threading
import time
from sys import exit
import threading

import pygame as pg
from xLPyBasics import Sentinels as df
from xLPyBasics.PathAPI import (
    Path,
    PathHandler, Search
)

# ———DATA———

ROBLOX_TEMP_SOUNDS_DIR = Path(tempfile.gettempdir(), "Roblox", "sounds")
SOUND_EXTENSION: str = ".wav"
SOUNDS_PATH: Path = Path("assets", "sounds", prepension=Path.get_meipass(Path.cwd()))

IDENTIFICATION_DEPTH = 300
IDENTIFIER_DEPTH = 300
IDENTIFIER_TYPE: str = "int32"

# default sounds options
class SoundOptions(Enum):
    # ShuttingDown = "shutting_down"
    Lobby = "lobby_enter"
    Exit = "exit_game"
    Test = "test_sound"
    Error = "error"
    AnglerError = "error_angler"
    PinkieError = "error_pinkie"
    EyefestationError = "error_eyefestation"
    Rabba = "rabba_rabba"

@dataclass(frozen=True, slots=True)
class VoiceOption:
    name: str
    weight: int

# voice options
class VoiceOptions(Enum):
    GIF = VoiceOption("GIF", 6)
    Mayer = VoiceOption("Mayer", 2)

VOICES_DISABLED_BY_DEFAULT = [
    VoiceOptions.GIF,
]

# category options
class CategoryOptions(Enum):
    Angler = "angler"
    Pinkie = "pinkie"
    Searchlights = "searchlights"
    Abomination = "abomination"
    Firewall = "firewall"
    Eyefestation1 = "eyefestation1"
    Eyefestation2 = "eyefestation2"
    Eyefestation3 = "eyefestation3"
    Enragement2 = "enragement2"
    Enragement3 = "enragement3"
    Enter = "enter"
    Crystal = "crystal"
    OxygenGardens = "gardens"
    Dredge = "dredge"
    NaviRoom = "navi"
    Ghost = "ghost"
    Death = "death"
    Random = "random"

# voice storage for sounds
class Voice:
    def __init__(self: Self, voice: VoiceOptions):
        self.is_enabled: bool = True
        self.path = SOUNDS_PATH.appended(voice.value.name)
        self.categories: dict[CategoryOptions, list[pg.mixer.Sound]] = {}

type SoundKey = SoundOptions|tuple[VoiceOptions, CategoryOptions]

sounds: dict[SoundOptions, pg.mixer.Sound]|df.Type.Unset = df.Value.Unset
voices: dict[VoiceOptions, Voice]|df.Type.Unset = df.Value.Unset

volume_level: float = 1
playing_sounds: dict[SoundKey, pg.mixer.Channel] = {}
playing_sounds_lock = threading.Lock()

do_test_sound = True
test_sound_locked = 0

# ———METHODS———

_was_inited: bool = False
def init() -> None:
    global _was_inited
    global sounds, voices

    # don't init twice
    if _was_inited: raise RuntimeError("cannot initialize twice")
    _was_inited = True

    # check that roblox directory exists
    if not PathHandler(ROBLOX_TEMP_SOUNDS_DIR).exists_dir:
        from tkinter import messagebox
        messagebox.showerror("No Roblox", "roblox is not installed on this machine or a game has not yet been opened with it ⇒ install roblox and open a game")
        exit()

    # ║ defaults
    sounds = {}
    for sound_opt in SoundOptions:
        curr_loc = PathHandler(SOUNDS_PATH.tempp(sound_opt.value, extension=SOUND_EXTENSION))
        if curr_loc.exists_dir: continue
        sounds[sound_opt] = pg.mixer.Sound(curr_loc.path.get())

    # ║ voices
    voices = {}
    for voice_opt in VoiceOptions:
        # create voice
        curr_voice = Voice(voice_opt)
        voices[voice_opt] = curr_voice

        # for every category
        for cat_opt in CategoryOptions:
            curr_loc = PathHandler(curr_voice.path.appended(cat_opt.value))
            if not curr_loc.exists_dir: continue

            # for every sound file in the curr path
            for file in curr_loc.read_dir(
                Search.Settings(
                    extensionȿ=SOUND_EXTENSION
                ),
                do_iter=True
            ):
                # create category if needed
                if (cat_opt not in curr_voice.categories.keys()):
                    curr_voice.categories[cat_opt] = []

                # get sound
                curr_voice.categories[cat_opt].append(pg.mixer.Sound(file.path.get()))

    # ║ disable default voices
    for voice in VOICES_DISABLED_BY_DEFAULT: voices[voice].is_enabled = False

# delete all temp sounds
def delete_temp_sounds() -> None:
    # for every roblox sound
    for file in PathHandler(ROBLOX_TEMP_SOUNDS_DIR).read_dir(do_iter=True):
        # try to delete it
        try: file.remove()
        except (PermissionError, OSError): pass # don't delete this file

def get_playing_sound(sound: SoundKey) -> pg.mixer.Channel|df.Type.Invalid:
    global playing_sounds, playing_sounds_lock
    with playing_sounds_lock:
        if sound not in playing_sounds: return df.Value.Invalid
        return playing_sounds[sound]

def get_enabled_voices() -> Iterator[tuple[VoiceOptions, Voice]]:
    """get a iterator of enabled voices only"""
    return ((voice_opt, voice) for voice_opt, voice in voices.items() if voice.is_enabled)

def _get_random_voice(with_category: CategoryOptions) -> VoiceOptions:
    """gets a random voice

    Args:
        with_category (CategoryOptions): the category this voice must have to be selected

    Returns:
        VoiceOptions: a random voice with the category
    """
    global voices

    # loop until no voices are left, trying to find a random
    voices_left: list[VoiceOptions] = list(voice[0] for voice in get_enabled_voices()) # get a list of enabled voices
    while len(voices_left) > 0:
        # create a list of all voice options (which are enabled) and shuffle it 
        total_active_weight: int = sum([voice_opt.value.weight for voice_opt in voices_left]) # get weight for voices left
        random_weighted_value = random.randint(0, (total_active_weight - 1)) # get a random weighted value
        options: list[VoiceOptions] = voices_left.copy() # copy of voices left used for finding the voice within the right weighted bracket
        while len(options) > 0:
            option = options.pop() # remove option at start
    
            # substract the weight and check if the value is found
            random_weighted_value -= option.value.weight
            if (random_weighted_value <= 0): 
                # check if option has cat
                if with_category not in voices[option].categories: 
                    voices_left.remove(option) # remove from options
                    break # will continue outer
                return option # return the option
            
    raise RuntimeError(f"no voice contains a sound for ⸉{with_category.name}⸉")

def stop_sound(sound: SoundKey) -> None:
    """stop a sound"""
    global playing_sounds, playing_sounds_lock

    with playing_sounds_lock:
        if sound not in playing_sounds: return # do nothing, not playing
        playing = playing_sounds[sound]
        playing.stop()
        del playing_sounds[sound]

def stop_sounds() -> None:
    """stops all playing sounds"""
    global playing_sounds
    playing_sounds_dup = playing_sounds.copy() # duplicate to avoid mutating the dict being looped
    for sound in playing_sounds_dup.keys(): stop_sound(sound)

def play_sound(
    sound: SoundOptions|CategoryOptions, 
    use_voice: VoiceOptions|df.Type.Alls = df.Value.Alls,
    do_stop: bool = False
) -> SoundKey:
    """plays a sound

    Args:
        sound (SoundOptions | CategoryOptions): the sound to play
        do_random (bool | df.Type.Alls, optional): the voice to use ╎ uses a random voice if set to All ╎ has no effect if sound isn't categoric. Defaults to All.
        do_stop (bool, optional): whether to stop all other playing sounds before playing. Defaults to False.

    Returns:
        SoundKey: the sound key of the sound played
    """
    global voices, sounds
    global playing_sounds, volume_level

    # do stop
    if do_stop: stop_sounds()

    # check if sound can use a voice
    playing_key: SoundKey
    playing_sound: pg.mixer.Sound
    if isinstance(sound, CategoryOptions):
        # get voice & check if voice exists for the sound
        if df.Check.is_alls(use_voice): use_voice = _get_random_voice(sound)
    
        # pick a random sound
        curr_sound_count = len(voices[use_voice].categories[sound])
        random_index = random.randint(0, (curr_sound_count - 1))
        random_sound = voices[use_voice].categories[sound][random_index]
        playing_key = (use_voice, sound)
        playing_sound = random_sound
    elif isinstance(sound, SoundOptions): 
        playing_key = sound
        playing_sound = sounds[sound]
    else: 
        raise TypeError(f"passed `sound` is not of type `SoundOptions` ꭉ `CategoryOptions`: {type(sound)}")

    # index & play
    stop_sound(playing_key) # stop sound if it's already playing
    playing_channel = playing_sound.play()
    playing_channel.set_volume(volume_level)
    with playing_sounds_lock:
        playing_sounds[playing_key] = playing_channel

    # schedule remover
    def remove_playing(sound: SoundKey) -> None:
        global playing_sounds
        channel = get_playing_sound(sound)
        if df.Check.is_invalid(channel): return # already stopped: do nothing
        while channel.get_busy(): time.sleep(0.2)
        stop_sound(sound)
    threading.Thread(
        target=remove_playing,
        args=(playing_key,),
        daemon=True
    ).start()
    return playing_key

def set_volume(
    volume: int, 
    do_play_test: bool = False
) -> None:
    """set the volume of all upcoming & playing sounds"""
    global volume_level
    volume_level = int(volume) / 100 # change volume for new sounds
    for _, sound in playing_sounds.items(): sound.set_volume(volume_level) # change volume of playing sounds

    # only if other sounds aren't playing and test is enabled, play a test sound
    if (
        do_play_test
        and ( # no sounds playing or only test sound playing
            (len(playing_sounds) == 0)
            or (
                (len(playing_sounds) == 1)
                and (next(iter(playing_sounds), None) == SoundOptions.Test)
            )
        )
    ): play_sound(SoundOptions.Test) 
