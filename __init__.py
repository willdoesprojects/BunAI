# -*- coding: utf-8 -*-

# BunAI 
#
# Copyright (C) 2025  William N. (willdoesprojects)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version, with the additions
# listed at the end of the accompanied license file.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# NOTE: This program is subject to certain additional terms pursuant to
# Section 7 of the GNU Affero General Public License.  You should have
# received a copy of these additional terms immediately following the
# terms and conditions of the GNU Affero General Public License which
# accompanied this program.
#
# If not, please request a copy through one of the means of contact
# listed here: <https://github.com/willdoesprojects>.
#
# Any modifications to this file must keep this entire header intact.

if __name__ != "__main__":
    from aqt import mw
    from . import bunai

    if mw:
        mw.bunai = bunai.BunAI(mw)
else:
    print("This is an Add-On for the application Anki! Please download in order to run the add on.")
