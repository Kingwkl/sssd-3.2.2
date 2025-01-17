# Authors:
#  Stephen Gallagher <sgallagh@redhat.com>
#
# Copyright (C) 2009  Red Hat
# see file 'COPYING' for use and warranty information
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
Python-level packaging using distutils.
"""

from distutils.core import setup

setup(
    name='SSSDConfig',
    version='2.2.3',
    license='GPLv3+',
    url='https://pagure.io/SSSD/sssd/',
    packages=['SSSDConfig'],
)
