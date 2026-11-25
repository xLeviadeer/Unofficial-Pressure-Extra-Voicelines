from typing import (
    Self
)
from enum import Enum
import tempfile
import random
from dataclasses import dataclass
import threading
import time

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
    Random = "random"

# voice storage for sounds
class Voice:
    def __init__(self: Self, voice: VoiceOptions):
        self.is_enabled: bool = True
        self.path = SOUNDS_PATH.appended(voice.value.name)
        self.categories: dict[CategoryOptions, list[pg.mixer.Sound]] = {}

sounds: dict[SoundOptions, pg.mixer.Sound]|df.Type.Unset = df.Value.Unset
voices: dict[VoiceOptions, Voice]|df.Type.Unset = df.Value.Unset

volume_level: float = 1
playing_sounds: list[pg.mixer.Channel] = []

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

# temp disable test sound playing
def _temp_disable_test_sound(channel: pg.mixer.Channel):
    global do_test_sound, test_sound_locked
    def re_enable_test_sound_playability(subchannel: pg.mixer.Channel) -> None:
        global do_test_sound, test_sound_locked
        while subchannel.get_busy(): time.sleep(0.1)
        if (test_sound_locked <= 1):
            do_test_sound = True
        test_sound_locked -= 1
    do_test_sound = False
    test_sound_locked += 1
    threading.Thread(
        target=re_enable_test_sound_playability,
        args=(channel,),
        daemon=True
    ).start()

# play sound default
def play_sound_default(sound: SoundOptions) -> pg.mixer.Channel:
    global volume_level
    global sounds

    # play sound
    sounds[sound].set_volume(volume_level)
    channel = sounds[sound].play()
    _temp_disable_test_sound(channel) # temp disable test sound playing
    
    # return channel
    return channel

# play sound based on voice + category
    # returns None when the category cannot be found for this voice
def play_sound_categoric(voice: VoiceOptions, category: CategoryOptions) -> pg.mixer.Channel|None:
    global voices
    global volume_level

    # check if the category exists 
    if (category not in voices[voice].categories.keys()): return None 

    # get category length and check if it has no sounds
    curr_sound_count = len(voices[voice].categories[category])
    if (curr_sound_count < 1): return None

    # pick a random sound
    random_index = random.randint(0, (curr_sound_count - 1))
    random_sound = voices[voice].categories[category][random_index]

    # play sound
    random_sound.set_volume(volume_level)
    channel = random_sound.play()
    _temp_disable_test_sound(channel) # temp disable test sound playing

    # return channel
    return channel

# volume set function
def set_volume(volume: int) -> None:
    global volume_level, playing_sounds
    global do_test_sound

    # inital checks & volume
    if (not do_test_sound): return # if test sound can be played
    volume_level = int(volume) / 100 # change volume

    # stop/remove all currently playing sounds
    if (len(playing_sounds) != 0):
        for sound in playing_sounds:
            if (sound.get_busy()):
                sound.stop()
                playing_sounds.remove(sound)
            else:
                playing_sounds.remove(sound)

    # play one test sound
    current = play_sound_default(SoundOptions.Test)
    playing_sounds.append(current)

# get the total active voices weight
def get_total_active_weight() -> int:
    global voices
    return sum([voice_opt.value.weight for voice_opt, voice in voices.items() if voice.is_enabled])

# get random voice by active weight
def _get_random_voice() -> VoiceOptions:
    global voices

    # create a list of all voice options (which are enabled) and shuffle it 
    random_weighted_value = random.randint(0, (get_total_active_weight() - 1)) # get a random weighted value
    options = [voice_opt for voice_opt in VoiceOptions if voices[voice_opt].is_enabled]
    random.shuffle(options)
    while len(options) > 0:
        option = options[0]

        # substract the weight and check if the value is found
        random_weighted_value -= option.value.weight
        if (random_weighted_value <= 0): return option # return the option
        options.pop(0) # remove option at start

# play random category sound
def play_sound_categoric_random(category: CategoryOptions) -> pg.mixer.Channel:
    # attempt to play sounds until one with a category is found
    while True:
        randomVoice = _get_random_voice() # get a random voice
        channel: pg.mixer.Channel|None = play_sound_categoric(randomVoice, category) # try to play the sound
        if channel != None: return channel # if successful (channel returned), return channel (break)