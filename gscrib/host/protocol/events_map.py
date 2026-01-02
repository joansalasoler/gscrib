# -*- coding: utf-8 -*-

# Gscrib. Supercharge G-code with Python.
# Copyright (C) 2026 Joan Sala <contact@joansala.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from . import events


# Maps response prefixes to event types
EVENTS_MAP = (
    ('!!', events.DeviceFaultEvent),
    ('[', events.DeviceFeedbackEvent),
    ('//', events.DeviceDebugEvent),
    ('<', events.DeviceFeedbackEvent),
    ('ALARM:', events.DeviceFaultEvent),
    ('busy:', events.DeviceBusyEvent),
    ('error:', events.DeviceErrorEvent),
    ('Error:', events.DeviceErrorEvent),
    ('fatal:', events.DeviceFaultEvent),
    ('Grbl', events.DeviceOnlineEvent),
    ('grbl', events.DeviceOnlineEvent),
    ('ok', events.DeviceReadyEvent),
    ('Resend:', events.DeviceResendEvent),
    ('resend:', events.DeviceResendEvent),
    ('rs:', events.DeviceResendEvent),
    ('start', events.DeviceOnlineEvent),
    ('wait', events.DeviceWaitEvent),
)
