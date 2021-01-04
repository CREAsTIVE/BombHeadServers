# Copyright (c) 2020 Roman Trapeznikov
"""The ExtendedGlow - BombSquad modification's Python module"""

# ba_meta require api 6
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING

from dataclasses import dataclass
from enum import Enum
import ba

if TYPE_CHECKING:
    from typing import Optional, Any, Tuple

ENABLE_LEGACY_CODES = True


class InvalidCodeError(Exception):
    """Invalid Glow code"""


class GlowFunction:
    """Glow function, used for calculate color/highlight"""

    class CalcFunc(Enum):
        """Glow calculate function"""
        MUL = '*'

    class StabilizeFunc(Enum):
        """Glow stabilize function"""
        DIVMIN = '/'
        DIVMED = ':'
        DIVAVG = '\\'
        ONLYMAX = 'M'
        NONE = '0'

    def __init__(self, funcstr: str):
        if ENABLE_LEGACY_CODES:
            if funcstr == '1':
                self.calc_func = self.CalcFunc.MUL
                self.stabilize_func = self.StabilizeFunc.ONLYMAX
                return
            if funcstr == '0':
                self.calc_func = self.CalcFunc.MUL
                self.stabilize_func = self.StabilizeFunc.NONE
                return
        if len(funcstr) != 2:
            raise InvalidCodeError('funcstr length must be 2')
        try:
            self.calc_func = self.CalcFunc(funcstr[0])
            self.stabilize_func = self.StabilizeFunc(funcstr[1])
        except ValueError as exc:
            raise InvalidCodeError('Invalid funcstr') from exc

    def calc(self, color: Tuple[float, float, float],
             k: float) -> Tuple[float, float, float]:
        """Calculates color"""
        # pylint: disable=too-many-branches,too-many-return-statements
        if self.stabilize_func == self.StabilizeFunc.DIVMIN:
            new_color = (0.0, 0.0, 0.0)
            if self.calc_func == self.CalcFunc.MUL:
                new_color = (color[0] * k, color[1] * k, color[2] * k)
            new_color_min = abs(min(new_color, key=abs))
            if new_color_min < 1:
                return new_color
            return (new_color[0] / new_color_min / 2,
                    new_color[0] / new_color_min / 2,
                    new_color[0] / new_color_min / 2)
        if self.stabilize_func == self.StabilizeFunc.DIVMED:
            new_color = (0, 0, 0)
            if self.calc_func == self.CalcFunc.MUL:
                new_color = (color[0] * k, color[1] * k, color[2] * k)
            new_color_med = sorted(color, key=abs)[1]
            if new_color_med < 1:
                return new_color
            return (new_color[0] / new_color_med, new_color[0] / new_color_med,
                    new_color[0] / new_color_med)
        if self.stabilize_func == self.StabilizeFunc.DIVAVG:
            new_color = (0, 0, 0)
            if self.calc_func == self.CalcFunc.MUL:
                new_color = (color[0] * k, color[1] * k, color[2] * k)
            new_color_avg = sum(color) / 3
            if new_color_avg < 1:
                return new_color
            return (new_color[0] / new_color_avg, new_color[0] / new_color_avg,
                    new_color[0] / new_color_avg)
        if self.stabilize_func == self.StabilizeFunc.ONLYMAX:
            color_max = max(color, key=abs)
            if self.calc_func == self.CalcFunc.MUL:
                return (color[0] * k if color[0] == color_max else color[0],
                        color[1] * k if color[1] == color_max else color[1],
                        color[2] * k if color[2] == color_max else color[2])
        if self.stabilize_func == self.StabilizeFunc.NONE:
            if self.calc_func == self.CalcFunc.MUL:
                return (color[0] * k, color[1] * k, color[2] * k)
        return color
        # pylint: enable=too-many-branches,too-many-return-statements


@dataclass
class Glow:
    """Glow data"""
    glow_name: str
    color_factor: float
    highlight_factor: float
    color_function: GlowFunction
    highlight_function: GlowFunction


class ExtendedGlow:
    """Static class that contains methods for internal ExtendedGlow logic"""

    code_limits = (-30.0, 30.0)

    @classmethod
    def limit(cls, value: float):
        """Returns value if it's lies in a given interval else one of border"""
        return max(cls.code_limits[0], min(cls.code_limits[1], value))

    @classmethod
    def parse_profile_name(cls, name: str) -> Optional[Glow]:
        """Parses profile name ans searches glow codes"""
        codes = name.split(',')
        if len(codes) not in (3, 5):
            return None
        extra_args = len(codes) == 5
        glow_name = codes[0]

        try:
            return Glow(
                glow_name=glow_name,
                color_factor=cls.limit(float(codes[1])),
                highlight_factor=cls.limit(float(codes[2])),
                color_function=GlowFunction(codes[3] if extra_args else '*M'),
                highlight_function=GlowFunction(
                    codes[3] if extra_args else '*M'))
        except (ValueError, InvalidCodeError):
            # raise InvalidCodeError
            return None


class ExtendedChooser(ba.Chooser):
    """Replacement for ba.Chooser class"""

    def __init__(self, *args, **kwargs):
        self._glows: Dict[str, Glow] = {}
        self._glow_name: Optional[str] = None
        self._has_glow_codes = False
        super().__init__(*args, **kwargs)

    def _getname(self, full: bool = False) -> str:
        name = super()._getname(full=full)
        for glow_name in self._glows:
            if name.startswith(glow_name):
                return name[len(glow_name):]
        return name

    def _get_glow_codes_if_needed(self):
        if self._has_glow_codes:
            return
        self._has_glow_codes = True
        for profilename in self._profilenames:
            glow = ExtendedGlow.parse_profile_name(profilename)
            if glow:
                self._glows[glow.glow_name] = glow

    def update_from_profile(self) -> None:
        self._get_glow_codes_if_needed()
        super().update_from_profile()
        self._glow_name = None
        for glow_name in self._glows:
            if self._profilename.startswith(glow_name):
                self._glow_name = glow_name
                break
        glow: Glow = self._glows.get(self._glow_name)
        if glow:
            self._color = glow.color_function.calc(self._color,
                                                   glow.color_factor)
            self._highlight = glow.highlight_function.calc(
                self._color, glow.highlight_factor)
        self._update_icon()
        self._update_text()


# ba_meta export plugin
class ExtendedGlowChooserPlugin(ba.Plugin):
    """Extended glow in game and lobby"""

    def on_app_launch(self) -> None:
        self.do_redefine()

    def do_redefine(self) -> None:
        """Redefines ba.Chooser"""
        # pylint: disable=redefined-outer-name,protected-access
        import ba._lobby
        ba._lobby.Chooser = ExtendedChooser
        # pylint: enable=redefined-outer-name,protected-access


# ba_meta export plugin
class ExtendedGlowUIPlugin(ba.Plugin):
    """Extended glow in character menu"""

    def on_app_launch(self) -> None:
        self.do_redefine()

    def do_redefine(self) -> None:
        """Redefines the profile menu for ExtendedGlow support"""
