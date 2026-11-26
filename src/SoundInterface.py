from typing import Self
from sys import exit
from abc import abstractmethod

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QSlider, QCheckBox,
    QGridLayout,
    QVBoxLayout, QHBoxLayout
)
from PySide6.QtGui import (
    QIcon
)
from xLPyBasics import Sentinels as df
from xLPyBasics.PathAPI import (
    Path
)
from xLPyBasics.ConsoleAPI import LoggerRegistry

import Core as Core
from Core import (
    LogChannel
)
import Sounds
from Sounds import (
    VoiceOptions
)
from ModeManager import (
    ModeOptions
)

ICON_PATH = Path("assets", "icon.ico", prepension=Path.get_meipass(Path.cwd()))

class VolumeSlider(QWidget):
    def __init__(self: Self, starting_volume: int) -> None:
        super().__init__()

        # validate range
        if not isinstance(starting_volume, int): raise TypeError("`starting_volume` must be an integer")
        if (
            (starting_volume < 0)
            or (starting_volume > 100)
        ): raise ValueError(f"`starting_volume` cannot be less than 0 or greater than 100: {starting_volume}")

        self.__do_update_vol: bool = True

        self.__box = QVBoxLayout()
        self.__label = QLabel()
        self.__box.addWidget(self.__label)
        self.__slider = QSlider(Qt.Orientation.Horizontal)
        self.__slider.setRange(0, 100)
        self.__slider.valueChanged.connect(lambda vol: self.set_volume(vol, True))
        self.__slider.setValue(starting_volume) # will run `set_volume`
        self.__box.addWidget(self.__slider)
        self.setLayout(self.__box)

    def set_volume(
        self: Self, 
        vol: int,
        do_play_test: bool = False
    ) -> None:
        # validate range
        if not isinstance(vol, int): raise TypeError("`vol` must be an integer")
        if (
            (vol < 0)
            or (vol > 100)
        ): raise ValueError(f"`vol` cannot be less than 0 or greater than 100: {vol}")

        # check if volume setting is enabled
        if not self.__do_update_vol: return # do nothing

        # set
        self.__label.setText(f"Volume: {vol}")
        Sounds.set_volume(vol, do_play_test=do_play_test)

        # change slider level
        if self.__slider.value() != vol: # ⌄ gates from recursively running the set volume method 
            self.__do_update_vol = False
            self.__slider.setValue(vol)
            self.__do_update_vol = True

class Toggle(QWidget):
    @property
    def is_toggled(self: Self) -> bool: return self._check_box.isChecked()
    
    def __init__(self: Self, label: str, initial_state: bool = False) -> None:
        super().__init__()

        self.__box = QHBoxLayout()
        self.__box.setContentsMargins(0, 0, 0, 0)
        self._check_box = QCheckBox()
        self._check_box.setChecked(initial_state)
        self._check_box.toggled.connect(self._on_toggled)
        self.__box.addWidget(self._check_box, stretch=0)
        self.__label = QLabel(label)
        self.__label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.__box.addWidget(self.__label, stretch=1)
        self.setLayout(self.__box)

    @abstractmethod
    def _on_toggled(self: Self, state: bool) -> None: ...

class ModeToggle(Toggle):
    __mode: ModeOptions

    def __init__(
        self: Self, 
        mode: ModeOptions
    ) -> None:
        super().__init__(mode.value.name, mode.value.is_enabled)
        self.__mode = mode
        self.__mode.value.on_changed.subscribe(self.__on_state_changed)

    def __on_state_changed(self: Self, state: bool) -> None:
        if self.is_toggled != state:
            print(state)
            self._check_box.setChecked(state) # will set voice state also

    def _on_toggled(self: Self, state: bool) -> None:
        if self.__mode.value.is_enabled != state:
            LoggerRegistry.log_at(LogChannel.SettingChange, f"set mode ⸉{self.__mode.name}⸉ to {state}")
            self.__mode.value.is_enabled = state
        if not df.Check.is_empty(self.__mode.value.linked_voice): 
            if Sounds.voices[self.__mode.value.linked_voice].is_enabled != state:
                Sounds.voices[self.__mode.value.linked_voice].is_enabled = state

class VoiceToggle(Toggle):
    __voice: VoiceOptions

    def __init__(self: Self, voice: VoiceOptions) -> None:
        super().__init__(voice.value.name, Sounds.voices[voice].is_enabled)
        self.__voice = voice

    def _on_toggled(self: Self, state: bool) -> None:
        if Sounds.voices[self.__voice].is_enabled != state:
            LoggerRegistry.log_at(LogChannel.SettingChange, f"set voice ⸉{self.__voice.name}⸉ to {state}")
            Sounds.voices[self.__voice].is_enabled = state

class ToggleGrid[T: Toggle](QWidget):
    __cols: int
    __curr_col: int
    __curr_row: int 

    def __init__(
        self: Self,
        label: str,
        cols: int
    ) -> None:
        super().__init__()

        self.__cols = cols
        self.__curr_col = 0
        self.__curr_row = 0

        self.__box = QVBoxLayout()
        self.__label = QLabel(label)
        self.__box.addWidget(self.__label)
        self.__grid = QGridLayout() # needs parent widget since it is being placed inside of another layout
        for i in range(cols): self.__grid.setColumnStretch(i, 1)
        self.__box.addLayout(self.__grid) # ⌃ see above comment
        self.setLayout(self.__box)

    def add_item(self: Self, item: T) -> None:
        self.__grid.addWidget(item, self.__curr_row, self.__curr_col)
        self.__curr_col += 1
        if self.__curr_col >= self.__cols:
            self.__curr_col = 0
            self.__curr_row += 1

class ModeTogglesGrid(ToggleGrid[ModeToggle]):
    def add_mode(self: Self, mode: ModeOptions) -> None:
        mode_toggle = ModeToggle(mode)
        self.add_item(mode_toggle)

class VoiceToggleGrid(ToggleGrid[VoiceToggle]): 
    def add_voice(self: Self, voice: VoiceOptions) -> None:
        voice_toggle = VoiceToggle(voice)
        self.add_item(voice_toggle)

class SoundInterface(QWidget):
    # ———CONSTRUCTOR———

    __singleton_exists: bool = False
    def __init__(
        self: Self, 
        icon: QIcon,
        width: int,
        voice_cols: int,
        mode_cols: int
    ) -> None:
        super().__init__()

        # singleton
        if type(self).__singleton_exists: raise RuntimeError("SoundInterface is a singleton and cannot be instantiated more than once")
        type(self).__singleton_exists = True

        # self window settings
        self.setWindowTitle(f"Unofficial Pressure Extra Voicelines v{Core.PROGRAM_VERSION}")
        self.setWindowIcon(icon)
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowStaysOnTopHint
        )

        # main grid
        self.__grid = QGridLayout()
        self.__grid.setContentsMargins(5, 5, 5, 5)
        self.__grid.setRowStretch(0, 0)
        self.__grid.setRowStretch(1, 0)
        self.__grid.setRowStretch(2, 0)
        self.setLayout(self.__grid)

        # sound slider
        self.__vol_slider = VolumeSlider(Sounds.SOUND_SCALE)
        self.__grid.addWidget(self.__vol_slider, 0, 0)

        # modes
        self.__mode_grid = ModeTogglesGrid("Modes", mode_cols)
        for mode in iter(ModeOptions): self.__mode_grid.add_mode(mode)
        self.__grid.addWidget(self.__mode_grid, 1, 0)

        # voices
        self.__voice_grid = VoiceToggleGrid("Voices", voice_cols)
        for voice in iter(VoiceOptions):
            if voice.value.hidden: continue
            self.__voice_grid.add_voice(voice)
        self.__grid.addWidget(self.__voice_grid, 2, 0)

        # set fixed size after adding everything
        self.adjustSize() # calculate size
        self.setFixedHeight(self.sizeHint().height()) # set as fixed
        self.setFixedWidth(width)

icon: QIcon

def launch() -> None:
    global app, icon

    # app
    app = QApplication()
    icon = QIcon(ICON_PATH.get())
    app.setWindowIcon(icon)

    # set handler & init runners
        # runners get ignored if they are disabled but always run
    handler = SoundInterface(icon, 400, 2, 3)
    handler.show()
    exit(app.exec())
