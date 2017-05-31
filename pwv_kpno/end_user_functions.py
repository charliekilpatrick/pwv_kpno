#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

#    This file is part of the pwv_kpno package.
#
#    The pwv_kpno package is free software: you can redistribute it and/or
#    modify it under the terms of the GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    The pwv_kpno package is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with pwv_kpno.  If not, see <http://www.gnu.org/licenses/>.

"""This document defines end user functions for the pwv_kpno package.
It relies heavily on the atmospheric transmission models generated by
create_atm_models.py and the modeled PWV level at Kitt Peak generated by
create_pwv_models.py. Functions contained in this document include
`available_data`, `update_models`, `measured_pwv`, `modeled_pwv`,
and `transmission`.
"""

import os
import pickle
from datetime import datetime

import numpy as np
from astropy.table import Table

from create_pwv_models import _update_suomi_data
from create_pwv_models import _update_pwv_model

__author__ = 'Daniel Perrefort'
__copyright__ = 'Copyright 2017, Daniel Perrefort'
__license__ = 'GPL V3'
__status__ = 'Development'


# Define necessary directory paths
ATM_MOD_DIR = './atm_models'  # Location of atmospheric models
PWV_TAB_DIR = './pwv_tables/'  # Where to write un-supplemented PWV data


def available_data():
    """Return a set of years for which SuomiNet data has been downloaded

    Return a set of years for which SuomiNet data has been downloaded to the
    local machine. Note that this function includes years for which any amount
    of data has been downloaded. It does not indicate if additional data has
    been released by SuomiNet."""

    with open('../CONFIG.txt', 'rb') as ofile:
        return pickle.load(ofile)


def update_models(year=None):
    """Download data from SuomiNet and update the locally stored PWV model

    Update the locally available SuomiNet data by downloading new data from the
    SuomiNet website. Use this data to create an updated model for the PWV
    level at Kitt Peak. If a year is provided, only update data for that year.
    If not, download all available data from 2017 onward that is not already
    on the local machine. Data for years from 2010 through 2016 is included
    with this package version by default.

    Args:
        year (int): A Year from 2010 onward

    Returns:
        updated_years (list): A list of years for which models where updated
    """

    # Check for valid args
    if not (isinstance(year, int) or year is None):
        raise TypeError("Argument 'year' must be an integer.")

    if isinstance(year, int) and year < 2010:
        raise ValueError('Cannot update models for years prior to 2010')

    if isinstance(year, int) and year > datetime.now().year:
        msg = 'Cannot update models for years greater than current year'
        raise ValueError(msg)

    # Update the local SuomiData and PWV models
    updated_years = _update_suomi_data(year)
    _update_pwv_model()

    return updated_years


def measured_pwv(year=None, month=None, day=None, hour=None):
    """Return an astropy table of PWV measurements for a given year

    Return an astropy table of precipitable water vapor (PWV) measurements
    taken by the SuomiNet project. The first column is named 'date' and
    contains the UTC datetime of each measurement. Successive columns are
    named using the SuomiNet IDs for different locations and contain PWV
    measurements for that location in millimeters. By default he returned
    table contains all locally available SuomiNet data. Results can be
    refined by year, month, day, and hour by using the key word arguments.

    Args:
        year  (int): The year of the desired PWV data
        month (int): The month of the desired PWV data
        day   (int): The day of the desired PWV data
        hour  (int): The hour of the desired PWV data

    Returns:
        pwv_data (astropy.table.Table): A table of measured PWV values in mm
    """

    # Check for valid args
    if not (isinstance(year, int) or year is None):
        raise TypeError("Argument 'year' (pos 1) must be an integer.")

    elif year is None and month is not None:
        msg = "Argument 'month' (pos 2) specified without 'year' (pos 1)."
        raise ValueError(msg)

    if not (isinstance(month, int) or month is None):
        raise TypeError("Argument 'month' (pos 2) must be an integer.")

    elif month is None and day is not None:
        msg = "Argument 'day' (pos 3) specified without 'month' (pos 2)."
        raise ValueError(msg)

    if not (isinstance(day, int) or day is None):
        raise TypeError("Argument 'day' (pos 2) must be an integer.")

    elif day is None and hour is not None:
        msg = "Argument 'hour' (pos 4) specified without 'day' (pos 3)."
        raise ValueError(msg)

    if not (isinstance(hour, int) or hour is None):
        raise TypeError("Argument 'hour' (pos 4) must be an integer.")

    # Read in SuomiNet measurements from the master table
    pwv_data = Table.read(os.path.join(PWV_TAB_DIR, 'measured_pwv.csv'))

    # Convert UNIX timestamps to UTC
    pwv_data['date'] = np.vectorize(datetime.fromtimestamp)(pwv_data['date'])
    pwv_data['date'].unit = 'UTC'

    # Assign units to the remaining columns
    for colname in pwv_data.colnames:
        if colname != 'date':
            pwv_data[colname].unit = 'mm'

    # Refine results to only include datetimes indicated by kwargs
    if year:
        indx = np.vectorize(lambda x: x.year == year)(pwv_data['date'])

    else:
        return pwv_data

    if month:
        test_func = np.vectorize(lambda x: x.month == month)
        indx = np.logical_and(indx, test_func(pwv_data['date']))

    if day:
        test_func = np.vectorize(lambda x: x.day == day)
        indx = np.logical_and(indx, test_func(pwv_data['date']))

    if hour:
        test_func = np.vectorize(lambda x: x.hour == hour)
        indx = np.logical_and(indx, test_func(pwv_data['date']))

    return pwv_data[np.where(indx)[0]]


def modeled_pwv(year=None, month=None, day=None, hour=None):
    """Return an astropy table of the modeled PWV a given year

    Return an astropy table of the modeled precipitable water vapor (PWV) value
    at. The first column is named 'date' and contains the UTC datetime of each
    modeled value. The second column is named 'pwv', and contains PWV values in
    millimeters. By default he returned table contains all locally available
    SuomiNet data. Results can be refined by year, month, day, and hour by
    using the key word arguments.

    Args:
        year  (int): The year of the desired PWV data
        month (int): The month of the desired PWV data
        day   (int): The day of the desired PWV data
        hour  (int): The hour of the desired PWV data in 24-hour format

    Returns:
        pwv_data (astropy.table.Table): A table of modeled PWV values in mm
    """

    # Check for valid args
    if not (isinstance(year, int) or year is None):
        raise TypeError("Argument 'year' (pos 1) must be an integer.")

    elif year is None and month is not None:
        msg = "Argument 'month' (pos 2) specified without 'year' (pos 1)."
        raise ValueError(msg)

    if not (isinstance(month, int) or month is None):
        raise TypeError("Argument 'month' (pos 2) must be an integer.")

    elif month is None and day is not None:
        msg = "Argument 'day' (pos 3) specified without 'month' (pos 2)."
        raise ValueError(msg)

    if not (isinstance(day, int) or day is None):
        raise TypeError("Argument 'day' (pos 2) must be an integer.")

    elif day is None and hour is not None:
        msg = "Argument 'hour' (pos 4) specified without 'day' (pos 3)."
        raise ValueError(msg)

    if not (isinstance(hour, int) or hour is None):
        raise TypeError("Argument 'hour' (pos 4) must be an integer.")

    # Read in SuomiNet measurements from the master table
    pwv_data = Table.read(os.path.join(PWV_TAB_DIR, 'modeled_pwv.csv'))

    # Convert UNIX timestamps to UTC
    pwv_data['date'] = np.vectorize(datetime.fromtimestamp)(pwv_data['date'])
    pwv_data['date'].unit = 'UTC'
    pwv_data['pwv'].unit = 'mm'

    # Refine results to only include datetimes indicated by kwargs
    if year:
        indx = np.vectorize(lambda x: x.year == year)(pwv_data['date'])

    else:
        return pwv_data

    if month:
        test_func = np.vectorize(lambda x: x.month == month)
        indx = np.logical_and(indx, test_func(pwv_data['date']))

    if day:
        test_func = np.vectorize(lambda x: x.day == day)
        indx = np.logical_and(indx, test_func(pwv_data['date']))

    if hour:
        test_func = np.vectorize(lambda x: x.hour == hour)
        indx = np.logical_and(indx, test_func(pwv_data['date']))

    return pwv_data[np.where(indx)[0]]


def transmission(date, airmass):
    """Return a model for the atmospheric transmission function due to PWV

    For a given datetime and airmass, return a model for the atmospheric
    transmission function due to precipitable water vapor (PWV) at Kitt Peak.
    The modeled transmission is returned as an astropy table with the columns
    'wavelength' and 'transmission'. Wavelength values range from 7000 to
    10,000 angstroms in x angstrom increments.

    Args:
        date (datetime.datetime): The datetime of the desired model
        airmass          (float): The airmass of the desired model

    Returns:
        trans_func (astropy.table.Table): The modeled transmission function

    """

    if not isinstance(date, datetime):
        raise TypeError("Argument 'date' (pos 1) must be a datetime instance")

    if not isinstance(airmass, (float, int)):
        msg = "Argument 'airmass' (pos 2) should be a float instance"
        raise TypeError(msg)

    # Determine the PWV level at zenith for the specified datetime
    pwv_model = Table.read(os.path.join(PWV_TAB_DIR, 'modeled_pwv.csv'))
    pwv_z = np.interp(date.timestamp(), pwv_model['date'], pwv_model['pwv'])

    # Determine the PWV level along line of sight
    pwv_los = pwv_z * airmass

    # Read in the atmospheric models from file
    atm_mods = {}
    for file in os.listdir(ATM_MOD_DIR):
        if file.endswith('.csv'):
            pwv_value = float(os.path.basename(file).split("_")[3])
            file_path = os.path.join(ATM_MOD_DIR, file)
            atm_mods[pwv_value] = Table.read(file_path)

    # Create a table to store the transmission function
    wavelengths = atm_mods[min(atm_mods.keys())]['wavelength']
    trans_func = Table(names=['wavelength', 'transmission'])

    # Calculate the transmission function
    for i, wvlngth in enumerate(wavelengths):
        # Get a list of the modeled transmission for each pwv level
        trans = [atm_mods[pwv]['transmission'][i] for pwv in atm_mods]

        # Interpolate to find the transmission for pwv_los
        interp_trans = np.interp(pwv_los, list(atm_mods.keys()), trans)
        trans_func.add_row([wvlngth, interp_trans])

    return trans_func
