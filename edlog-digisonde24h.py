#!/usr/bin/env python

# Documentation of the SAO format: https://ulcar.uml.edu/~iag/SAO-4.3.htm
# example usage:
# python ed-digisonde24h.py directory/TR169_YYYYDDD <output>
#
# directory = path to the digisonde data
# YYYY = year
# DDD = the day number of the year
# output = filename of the resulting plot (optional argument)
# if no output filename is given, the program just plot to screen
# comment out last line if you do not want output to screen

import glob
import math
import sys
from datetime import datetime
import calendar
import numpy as np
import matplotlib
# matplotlib.use('Agg')    # use the 'Agg' backend when $DISPLAY environment is not defined
import matplotlib.pyplot as plt

plt.rcParams["figure.figsize"] = (10, 4)


# function for reading groups of data from file taking arguments group number and length of each element in byte as
# defined in the documentation
def read_group(group_number, length_of_element):
    group = np.zeros(int(num_elements[group_number - 1]))
    for index in range(int(num_elements[group_number - 1])):
        if (index != 0) and ((index % round(120 / length_of_element)) == 0):
            f.read(2)
        # changed June 16th 2020 due to data file containing 'Infinit' instead of numbers in group 4 (scaled ionospheric..)
        temporary = f.read(length_of_element)
        if temporary.decode("utf-8") == ' Infinit':
            group[index] = b'9999.000'
        else:
            group[index] = temporary
    if int(num_elements[group_number - 1]) != 0:
        f.read(2)
    return group


# define empty list for height, frequency and time
height = []
ff = []
timeaxis = []

# dato = '2020095'
for filename in glob.glob(sys.argv[1] + '*.SAO'):
# for filename in glob.glob('today\\TR169_' + dato + '*.SAO'):
    f = open(filename, "rb")  # use this if filename is defined above

    # --------------------------------------------------
    # Data File Index - number of elements in each group
    # --------------------------------------------------

    num_elements = np.zeros(80)
    for i in range(80):
        if (i != 0) and ((i % round(120 / 3)) == 0):
            f.read(2)
        num_elements[i] = f.read(3)
    f.read(2)

    # --------------------------------
    # GROUP 1: Geophysical Constants
    # --------------------------------

    geophysical_constant = read_group(1, 7)

    # ----------------------------------------------------
    # GROUP 2: System Description and Operator's Message
    # ----------------------------------------------------

    if int(num_elements[1]) == 0:  # no system description and operators message
        system_description = ''
    elif int(num_elements[1]) == 1:  # system description only
        system_description = str(f.read(120))
    else:  # operators message included
        f.read(2)
        operator_message = str(f.read(120))

    if int(num_elements[1]) != 0:
        f.read(2)

    # ------------------------------------------
    # GROUP 3: Time Stamp and Sounder Settings
    # ------------------------------------------

    # Assuming Digisonde Portable Sounder (DPS) System (Table 4)
    time_and_sounder_settings = f.read(int(num_elements[2]))

    # sorting out information in group 3. Only a few of these variables are used later in the code (date and time),
    # but all variables are created for possible later use.
    version_indicator = time_and_sounder_settings[0:2].decode("utf-8")  # string (AA, FF or FE)
    year = int(time_and_sounder_settings[2:6])  # int (1976-...)
    day_of_year = int(time_and_sounder_settings[6:9])  # int (1-366)
    month = int(time_and_sounder_settings[9:11])  # int (1-12)
    day_of_month = int(time_and_sounder_settings[11:13])  # int (1-31)
    hour = int(time_and_sounder_settings[13:15])  # int (0-23)
    minute = int(time_and_sounder_settings[15:17])  # int (0-59)
    sec = int(time_and_sounder_settings[17:19])  # int (0-59)
    receiver_station_id = time_and_sounder_settings[19:22].decode("utf-8")  # string (000-999) - three digits
    transmitter_station_id = time_and_sounder_settings[22:25].decode("utf-8")  # string (000-999) - three digits
    DPS_schedule = int(time_and_sounder_settings[25:26])  # int (1-6)
    DPS_program = int(time_and_sounder_settings[26:27])  # int (1-7)
    start_frequency = time_and_sounder_settings[27:32].decode("utf-8")  # string (01000-25000)
    coarse_frequency = int(time_and_sounder_settings[32:36])  # int (1-2000)
    stop_frequency = time_and_sounder_settings[36:41].decode("utf-8")  # string (01000-25000)
    DPS_fine_frequency_step = time_and_sounder_settings[41:45].decode("utf-8")  # string (0000-9999)
    multiplexing_disabled = int(time_and_sounder_settings[45:46])  # int (0,1) -> 0=enabled, 1=disabled
    number_of_DPS_small_steps_in_a_scan = time_and_sounder_settings[46:47].decode("utf-8")  # string (1-F)
    DPS_phase_code = time_and_sounder_settings[47:48].decode("utf-8")  # string (1-4, 9-C)
    alternative_antenna_setup = int(time_and_sounder_settings[48:49])  # int (0,1) -> 0=standard, 1=alternative
    DPS_antenna_options = time_and_sounder_settings[49:50].decode("utf-8")  # string (0 to F)
    total_FFT_samples = int(time_and_sounder_settings[50:51])  # int (3-7)
    DPS_radio_silent_mode = int(time_and_sounder_settings[51:52])  # int (0,1) -> 1=no transmission
    pulse_repetition_rate = int(time_and_sounder_settings[52:55])  # int (0-999)
    range_start = int(time_and_sounder_settings[55:59])  # int (0-9999)
    DPS_range_increment = time_and_sounder_settings[59:60].decode("utf-8")  # string (2,5,A) - 2=2.5km, 5=5km, A=10km
    number_of_ranges = int(time_and_sounder_settings[60:64])  # int (1-9999)
    scan_delay = int(time_and_sounder_settings[64:68])  # int (0-1500) (15km units)
    DPS_base_gain = time_and_sounder_settings[68:69].decode("utf-8")  # string (0-F, encoded)
    DPS_frequency_search_enabled = int(time_and_sounder_settings[69:70])  # int (0,1)
    DPS_operation_mode = int(time_and_sounder_settings[70:71])  # int (0-7), 0=vertical beam, 5=multi-beam
    ARTIST_enabled = int(time_and_sounder_settings[71:72])  # int (0,1)
    DPS_data_format = int(time_and_sounder_settings[72:73])  # int (0-6), 1=MMM, 4=RSF, 5=SBF
    printer_selection = int(time_and_sounder_settings[73:74])  # int (0,1,2), 0=no printer, 1=b/w, 2=color
    ionogram_thresholded_for_FTP_transfer = int(time_and_sounder_settings[74:76])  # int (0-20, encoded)
    high_interference_condition = int(time_and_sounder_settings[76:77])  # int (0,1)

    if int(num_elements[2]) != 0:
        f.read(2)

    # ---------------------------------------------
    # GROUP 4: Scaled Ionospheric Characteristics
    # ---------------------------------------------

    scaled_ionospheric_characteristics = read_group(4, 8)

    # -------------------------
    # GROUP 5: Analysis flags
    # -------------------------

    analysis_flags = read_group(5, 2)

    # ------------------------------------
    # GROUP 6: Doppler translation table
    # ------------------------------------

    doppler_translation_table = read_group(6, 7)

    # ------------------------------------------------------
    # GROUP 7: O-Trace points - f2 layer - Virtual heights
    # ------------------------------------------------------
    o_f2_virt_heights = read_group(7, 8)

    # ---------------------------------------------------
    # GROUP 8: O-Trace points - f2 layer - True heights
    # ---------------------------------------------------
    o_f2_true_heights = read_group(8, 8)

    # -------------------------------------------------
    # GROUP 9: O-Trace points - f2 layer - Amplitudes
    # -------------------------------------------------

    o_f2_amplitudes = read_group(9, 3)

    # -------------------------------------------------------
    # GROUP 10: O-Trace points - f2 layer - Doppler numbers
    # -------------------------------------------------------

    o_f2_doppler_numbers = read_group(10, 1)

    # --------------------------------------------
    # GROUP 11: O-Trace - f2 layer - Frequencies
    # --------------------------------------------

    o_f2_frequencies = read_group(11, 8)

    # -------------------------------------------------------
    # GROUP 12: O-Trace points - f1 layer - Virtual heights
    # -------------------------------------------------------

    o_f1_virt_heights = read_group(12, 8)

    # ----------------------------------------------------
    # GROUP 13: O-Trace points - f1 layer - True heights
    # ----------------------------------------------------

    o_f1_true_heights = read_group(13, 8)

    # --------------------------------------------------
    # GROUP 14: O-Trace points - f1 layer - Amplitudes
    # --------------------------------------------------

    o_f1_amplitudes = read_group(14, 3)

    # -------------------------------------------------------
    # GROUP 15: O-Trace points - f1 layer - Doppler numbers
    # -------------------------------------------------------

    o_f1_doppler_numbers = read_group(15, 1)

    # --------------------------------------------
    # GROUP 16: O-Trace - f1 layer - Frequencies
    # --------------------------------------------

    o_f1_frequencies = read_group(16, 8)

    # ------------------------------------------------------
    # GROUP 17: O-Trace points - E layer - Virtual heights
    # ------------------------------------------------------

    o_e_virt_heights = read_group(17, 8)

    # ---------------------------------------------------
    # GROUP 18: O-Trace points - E layer - True heights
    # ---------------------------------------------------

    o_e_true_heights = read_group(18, 8)

    # -------------------------------------------------
    # GROUP 19: O-Trace points - E layer - Amplitudes
    # -------------------------------------------------

    o_e_amplitudes = read_group(19, 3)

    # ------------------------------------------------------
    # GROUP 20: O-Trace points - E layer - Doppler numbers
    # ------------------------------------------------------

    o_e_doppler_numbers = read_group(20, 1)

    # --------------------------------------------------
    # GROUP 21: O-Trace points - E layer - Frequencies
    # --------------------------------------------------

    o_e_frequencies = read_group(21, 8)

    # -------------------------------------------------------
    # GROUP 22: X-Trace points - f2 layer - Virtual heights
    # -------------------------------------------------------

    x_f2_virt_heights = read_group(22, 8)

    # --------------------------------------------------
    # GROUP 23: X-Trace points - f2 layer - Amplitudes
    # --------------------------------------------------

    x_f2_amplitudes = read_group(23, 3)

    # -------------------------------------------------------
    # GROUP 24: X-Trace points - f2 layer - Doppler numbers
    # -------------------------------------------------------

    x_f2_doppler_numbers = read_group(24, 1)

    # --------------------------------------------
    # GROUP 25: X-Trace - f2 layer - Frequencies
    # --------------------------------------------

    x_f2_frequencies = read_group(25, 8)

    # -------------------------------------------------------
    # GROUP 26: X-Trace points - f1 layer - Virtual heights
    # -------------------------------------------------------

    x_f1_virt_heights = read_group(26, 8)

    # --------------------------------------------------
    # GROUP 27: X-Trace points - f1 layer - dmplitutes
    # --------------------------------------------------

    x_f1_amplitudes = read_group(27, 3)

    # -------------------------------------------------------
    # GROUP 28: X-Trace points - f1 layer - Doppler numbers
    # -------------------------------------------------------

    x_f1_doppler_numbers = read_group(28, 1)

    # ---------------------------------------------------
    # GROUP 29: X-Trace points - f1 layer - Frequencies
    # ---------------------------------------------------

    x_f1_frequencies = read_group(29, 8)

    # ------------------------------------------------------
    # GROUP 30: X-Trace points - E layer - Virtual heights
    # ------------------------------------------------------

    x_e_virt_heights = read_group(30, 8)

    # -------------------------------------------------
    # GROUP 31: X-Trace points - E layer - Amplitudes
    # -------------------------------------------------

    x_e_amplitudes = read_group(31, 3)

    # ------------------------------------------------------
    # GROUP 32: X-Trace points - E layer - Doppler numbers
    # ------------------------------------------------------

    x_e_doppler_numbers = read_group(32, 1)

    # --------------------------------------------------
    # GROUP 33: X-Trace points - E layer - Frequencies
    # --------------------------------------------------

    x_e_frequencies = read_group(33, 8)

    # -----------------------------------------
    # GROUP 34: Median amplitudes of F echoes
    # -----------------------------------------

    median_amplitudes_f_echoes = read_group(34, 3)

    # -----------------------------------------
    # GROUP 35: Median amplitudes of E echoes
    # -----------------------------------------

    median_amplitudes_e_echoes = read_group(35, 3)

    # ------------------------------------------
    # GROUP 36: Median amplitudes of ES echoes
    # ------------------------------------------

    median_amplitudes_es_echoes = read_group(36, 3)

    # ------------------------------------------------------------
    # GROUP 37: True heights coefficients f2 layer Umlcar method
    # ------------------------------------------------------------

    true_heights_coeff_f2_layer = read_group(37, 11)

    # ------------------------------------------------------------
    # GROUP 38: True heights coefficients f1 layer Umlcar method
    # ------------------------------------------------------------

    true_heights_coeff_f1_layer = read_group(38, 11)

    # -----------------------------------------------------------
    # GROUP 39: True heights coefficients E layer Umlcar method
    # -----------------------------------------------------------

    true_heights_coeff_e_layer = read_group(39, 11)

    # ----------------------------------------------------------
    # GROUP 40: Quazi-Parabolic segments fitted to the profile
    # ----------------------------------------------------------

    quazi_parabolic_segments = read_group(40, 20)

    # --------------------------------------
    # GROUP 41: Edit flags characteristics
    # --------------------------------------

    edit_flags = read_group(41, 1)

    # ------------------------------
    # GROUP 42: Valley description
    # ------------------------------

    valley_description = read_group(42, 11)

    # -------------------------------------------------------
    # GROUP 43: O-Trace points - Es layer - Virtual heights
    # -------------------------------------------------------

    o_es_virt_heights = read_group(43, 8)

    # --------------------------------------------------
    # GROUP 44: O-Trace points - Es layer - Amplitudes
    # --------------------------------------------------

    o_es_amplitudes = read_group(44, 3)

    # -------------------------------------------------------
    # GROUP 45: O-Trace points - Es layer - Doppler numbers
    # -------------------------------------------------------

    o_es_doppler_numbers = read_group(45, 1)

    # ---------------------------------------------------
    # GROUP 46: O-Trace points - Es layer - Frequencies
    # ---------------------------------------------------

    o_es_frequencies = read_group(46, 8)

    # --------------------------------------------------------------
    # GROUP 47: O-Trace points - E Auroral layer - Virtual heights
    # --------------------------------------------------------------

    o_ea_virt_heights = read_group(47, 8)

    # --------------------------------------------------
    # GROUP 48: O-Trace points - Es layer - Amplitudes
    # --------------------------------------------------

    o_ea_amplitudes = read_group(48, 3)

    # -------------------------------------------------------
    # GROUP 49: O-Trace points - Es layer - Doppler numbers
    # -------------------------------------------------------

    o_ea_doppler_numbers = read_group(49, 1)

    # ---------------------------------------------------
    # GROUP 50: O-Trace points - Es layer - Frequencies
    # ---------------------------------------------------

    o_ea_frequencies = read_group(50, 8)

    # --------------------------------
    # GROUP 51: True height profiles
    # --------------------------------

    true_heights = read_group(51, 8)

    # ------------------------------
    # GROUP 52: Plasma Frequencies
    # ------------------------------

    plasma_frequencies = read_group(52, 8)

    # ------------------------------
    # GROUP 53: Electron densities
    # ------------------------------

    electron_density = read_group(53, 8)

    # the next groups does not exist in the Ramfjordmoen digisonde SAO data, and are therefore not read since

    # -----------------------------------
    # GROUP 54: URSI Qualifying letters
    # -----------------------------------

    # ------------------------------------
    # GROUP 55: URSI Descriptive letters
    # ------------------------------------

    # ------------------------------------------------
    # GROUP 56: URSI Edit flags - traces and profile
    # ------------------------------------------------

    # -------------------------------------------------------------------------------------------
    # GROUP 57: Auroral E_Layer Profile Data - True heights coefficients Ea Layer Umclar method
    # -------------------------------------------------------------------------------------------

    # -------------------------------------------------------
    # GROUP 58: Auroral E_Layer Profile Data - True Heights
    # -------------------------------------------------------

    # -------------------------------------------------------------
    # GROUP 59: Auroral E_Layer Profile Data - Plasma Frequencies
    # -------------------------------------------------------------

    # -------------------------------------------------------------
    # GROUP 60: Auroral E_Layer Profile Data - Electron Densities
    # -------------------------------------------------------------

    f.close()

    height.append(list(np.array(true_heights)))

    ff.append(plasma_frequencies)

    length = len(list(np.array(true_heights)))

    timeaxis.append([hour + (minute + 7.5) / 60.] * length)

x = list(matplotlib.cbook.flatten(timeaxis))
y = list(matplotlib.cbook.flatten(height))
freq = list(matplotlib.cbook.flatten(ff))

today = datetime.now()
now = today.hour + today.minute / 60

# convert from frequency to number of electrons per cubic meter
col = []
for ix in range(len(freq)):
    col.append(math.log10((freq[ix] * 1e6) * (freq[ix] * 1000000) / 81.))

# plotting

x = np.array(x)
y = np.array(y)
col = np.array(col)

title = 'Ramfjordmoen Digisonde electron density ' + calendar.month_name[month] + ' ' + str(day_of_month) + ' ' + str(year)

fig, ax = plt.subplots()

cm = plt.cm.get_cmap('jet')
sc = plt.scatter(x, y, c=col, marker="s", s=24, cmap=cm)
# sc = plt.pcolormesh(x, y, col, cmap=cm) # this will fail..
if (year == today.year) and (month == today.month) and (day_of_month == today.day):
    plt.axvline(now, color='grey', alpha=0.5)
ax.grid(True, which='both')
ax.set_xlim(0, 24)
ax.set_ylim(0, 400)
ax.set_title(title)
ax.set_xlabel('Universal Time')
ax.set_ylabel('Altitude (km)')
plt.clim(vmin=10)
cbar = plt.colorbar(sc)
cbar.set_label('Electrons per cubic meter (log10)')

# write to file if argument is given
if len(sys.argv) == 3:
    savefilename = sys.argv[2]
    fig.savefig(savefilename)

# comment out if you do not want output to screen
plt.show()
