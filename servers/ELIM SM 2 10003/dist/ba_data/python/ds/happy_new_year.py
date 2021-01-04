# Copyright (c) 2020 Daniil Rakhov
# Copyright (c) 2020 Roman Trapeznikov
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

####################################################################
# Инструкция к моду:                                               #
# Первый плагин (SnowFall):                                        #
# - включает снегопад и изменяет освещение.                        #
#                                                                  #
# Второй плагин (HappyNewYear):                                    #
# - если вы сделаете перса с ником "Happy New Year",               #
# - у него будет скин Санты.                                       #
####################################################################
# Inscruction for mod:                                             #
# First plugin (SnowFall):                                         #
# - enabled a snowfall and edits lighting.                         #
#                                                                  #
# Secind plugin (HappyNewYear):                                    #
# - if you create character with "HappyNewYear" nickname,          #
# - it will have Santa skin.                                       #
####################################################################

# ba_meta require api 6
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Dict, Callable

import ba
import ba._activity
import ba._player
import _ba

import random


def redefine_activity(methods: Dict[str, Callable]) -> None:
    for n, func in methods.items():
        if hasattr(ba._activity.Activity, n):
            setattr(ba._activity.Activity, n + '_old',
                    getattr(ba._activity.Activity, n))
        setattr(ba._activity.Activity, n, func)


def redefine_player(methods: Dict[str, Callable]) -> None:
    for n, func in methods.items():
        if hasattr(ba._player.Player, n):
            setattr(ba._player.Player, n + '_old',
                    getattr(ba._player.Player, n))
        setattr(ba._player.Player, n, func)


def snowfall(self) -> None:
    self._snowfall_timer = ba.Timer(0.005,
                                    ba.WeakCall(self._emit_snowfall),
                                    repeat=True)


def emit_snowfall(self):
    bounds = self.map.get_def_bound_box('map_bounds') if getattr(
        self, 'map', None) else (
            -14.3569491031, -2.200293481, -18.507121877, 14.8787058369,
            11.999620949, 11.419771563000001)  # The Pad bounds (for main menu)

    position = (random.uniform(bounds[0], bounds[3]),
                random.uniform(bounds[4] * 1.15, bounds[4] * 1.45),
                random.uniform(bounds[2], bounds[5]))

    vel1 = ((-5.0 + random.random() * 30.0) *
            (-1.0 if position[0] > 0 else 1.0))

    vel = (vel1, -50.0, random.uniform(-20, 20))

    ba.emitfx(position=position,
              velocity=vel,
              count=5,
              scale=0.4 + random.random(), #0.4
              spread=0,
              chunk_type='spark')


def snowfall_on_begin(self) -> None:
    """Called once the previous ba.Activity has finished transitioning out.

    At this point the activity's initial players and teams are filled in
    and it should begin its actual game logic.
    """
    self.globalsnode.tint = (0.74, 0.74, 0.78)
    # self.globalsnode.tint = (1.4, 1.4, 1.6)
    self.globalsnode.ambient_color = (1, 1, 1)
    self.globalsnode.shadow_ortho = True
    self.globalsnode.vignette_outer = (0.86, 0.86, 0.86)
    self.globalsnode.vignette_inner = (0.95, 0.95, 0.99)
    self.globalsnode.vr_near_clip = 0.5
    self.snowfall()
    return# self.on_begin_old()


def happy_new_year_postinit(self, *args, **kwargs) -> None:
    self.postinit_old(*args, **kwargs)
    name = self.getname(full=True)
    if name == 'Happy New Year':
        self.character = 'Santa Claus'


def snowfall_main() -> None:
    redefine_activity({
        'snowfall': snowfall,
        '_emit_snowfall': emit_snowfall,
        'on_begin': snowfall_on_begin
    })


def happy_new_year_main() -> None:
    redefine_player({'postinit': happy_new_year_postinit})


