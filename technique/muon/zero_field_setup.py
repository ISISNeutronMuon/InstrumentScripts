from genie_python import genie as g
import time
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from builtins import range
from builtins import input

PV_AUTO_FEEDBACK_MODE = "TE:NDLT1205:ZFCNTRL_01:AUTOFEEDBACK"
PV_MAGNETIC_FIELD_STRENGTH = "TE:NDLT1205:ZFMAGFLD_01:FIELDSTRENGTH"

PV_SETPOINT_X = "TE:NDLT1205:ZFCNTRL_01:FIELD:X:SP"
PV_SETPOINT_Y = "TE:NDLT1205:ZFCNTRL_01:FIELD:Y:SP"
PV_SETPOINT_Z = "TE:NDLT1205:ZFCNTRL_01:FIELD:Z:SP"

POWER_SUPPLY_MAX = 100.00

class time():
    #pylint: disable=E0102
    @staticmethod
    def sleep(something):
        pass

class ZeroFieldSetupProcedure():
    """
    Class for setting up zero field procedure. Contains all the required function which can be run sequentially to
    to complete the set up
    """
    # pylint: disable=W0232

    def read_values(self):
        """
        Read corrected values from the OPI
        :return: corrected values for all axis
        """
        x = self.get_single_corrected_field_value("X")
        y = self.get_single_corrected_field_value("Y")
        z = self.get_single_corrected_field_value("Z")

        return x, y, z

    def get_magnitude(self):
        """
        Reads magnitude value from the OPI
        :return: magnitude of magnetic field
        """
        return g.get_pv(PV_MAGNETIC_FIELD_STRENGTH)

    def set_setpoints_to_zero(self, value_x, value_y, value_z):
        """
        Set all set points to 0
        :param value_x: target value for x axis
        :param value_y: target value for y axis
        :param value_z: target value for z axis
        :return: None
        """
        g.set_pv(PV_SETPOINT_X, value_x)
        g.set_pv(PV_SETPOINT_Y, value_y)
        g.set_pv(PV_SETPOINT_Z, value_z)

    def get_correlated_current_and_fields(self, plot=False):
        """
        Gets correlated current and corrected fields, 2 second wait before taking the field
        reading in all three axis
        :param plot: data to be plotted or not
        :return: correlated current and fields for each axis
        """
        iteration_number = 21

        current_x = []
        current_y = []
        current_z = []

        fields_x = []
        fields_y = []
        fields_z = []

        # after every 5% increase in current, wait for 2 second and read the field
        # in all three dimensions
        for x in range(iteration_number):
            current_x.append(((x - 10) / 10.0) * POWER_SUPPLY_MAX)
            current_y.append(((x - 10) / 10.0) * POWER_SUPPLY_MAX)
            current_z.append(((x - 10) / 10.0) * POWER_SUPPLY_MAX)

            time.sleep(2)

            fields_x.append(self.get_single_corrected_field_value("X"))
            fields_y.append(self.get_single_corrected_field_value("Y"))
            fields_z.append(self.get_single_corrected_field_value("Z"))

        if plot is True:
            plt.plot(current_x, fields_x, color="red", label="field X", marker="o")
            plt.plot(current_y, fields_y, color="green", label="field Y", marker="o")
            plt.plot(current_z, fields_z, color="blue", label="field Z", marker="o")
            plt.xticks([x for x in range(-100, 110, 10)])
            plt.xlabel("Current (A)")
            plt.ylabel("Field (mG)")
            plt.legend(loc="upper left")
            plt.show()

        return current_x, current_y, current_z, fields_x, fields_y, fields_z

    def calculate_coefficient_and_r_squared(self, x, y):
        """
        Calculates calibration coefficient and coefficient of determination
        :param x: current
        :param y: magnetic field
        :return: calibration coefficient and coefficient of determination
        """
        x = np.array(x)
        y = np.array(y)
        coefficient, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        return coefficient, (r_value ** 2)

    def calculate_noise(self, plot=False):
        """
        Calculates the noise in each axis over 20 seconds
        :param plot: data to be plotted or not
        :return: RMS noise value
        """
        auto_feedback_mode = 1
        manual = 0
        number_of_readings = 20

        mode = g.get_pv("TE:NDLT1205:ZFCNTRL_01:AUTOFEEDBACK")
        if mode == auto_feedback_mode:
            time.sleep(6)
        elif mode == manual:
            time.sleep(3)

        fields_x = []
        fields_y = []
        fields_z = []

        # 20 readings, one second apart
        for x in range(number_of_readings):
            fields_x.append(self.get_single_corrected_field_value("X"))
            fields_y.append(self.get_single_corrected_field_value("Y"))
            fields_z.append(self.get_single_corrected_field_value("Z"))
            time.sleep(1)

        # calculating variance of each field
        var_x = np.var(fields_x)
        var_y = np.var(fields_y)
        var_z = np.var(fields_z)

        rms = np.sqrt((var_x + var_y + var_z))

        if plot is True:
            time_in_seconds = [x for x in range(20)]
            plt.figure()
            plt.plot(time_in_seconds, fields_x, color="red", label="field X", marker="o")
            plt.plot(time_in_seconds, fields_y, color="green", label="field Y", marker="o")
            plt.plot(time_in_seconds, fields_z, color="blue", label="field Z", marker="o")
            plt.xticks(time_in_seconds)
            plt.xlabel("Time (sec)")
            plt.ylabel("Field (mG)")
            plt.legend(loc="upper left")
            plt.show()

        return rms

    def close_plot(self):
        """
        close all plot
        :return: none
        """
        plt.close("all")

    def check_if_stray_field_exist(self):
        """
        Check if there is huge stray field
        :return: True if there is huge stray field
        """
        measured_x, measured_y, measured_z = self.read_values()
        if (abs(measured_x) < 4000 and abs(measured_y)
                < 4000 and abs(measured_z) < 4000):
            return False
        return True

    def get_single_corrected_field_value(self, field_direction):
        """
        get single corrected field value
        :param field_direction: X, Y or Z
        :return: corrected field value from the given direction
        """
        return g.get_pv(
            "TE:NDLT1205:ZFMAGFLD_01:{}:CORRECTEDFIELD".format(field_direction))

    def ask_user_to_continue(self):
        """
        Ask user if they want to continue further
        :return:
        """
        reply = ""
        while reply != "Y" and reply != "N":
            reply = input("Would you like to continue? Y/N\n")
        if reply == "N":
            return "N"

    def get_instrument_name(self):
        """
        get instrument name
        :return: instrument name
        """
        return g.get_instrument()


def update_offset():
    """
    updates the offset so that the corrected field reading is 0 for each axis
    :return: None
    """
    x_raw_measurement = g.get_pv("TE:NDLT1205:ZFMAGFLD_01:DAQ:X:_RAW")
    y_raw_measurement = g.get_pv("TE:NDLT1205:ZFMAGFLD_01:DAQ:Y:_RAW")
    z_raw_measurement = g.get_pv("TE:NDLT1205:ZFMAGFLD_01:DAQ:Z:_RAW")

    x_new_offset = x_raw_measurement - 0
    y_new_offset = y_raw_measurement - 0
    z_new_offset = z_raw_measurement - 0

    g.set_pv("TE:NDLT1205:ZFMAGFLD_01:X:OFFSET", x_new_offset)
    g.set_pv("TE:NDLT1205:ZFMAGFLD_01:Y:OFFSET", y_new_offset)
    g.set_pv("TE:NDLT1205:ZFMAGFLD_01:Z:OFFSET", z_new_offset)


def run_all():
    """
    Run all the functions in order for set up
    :return:
    """
    while True:
        print("***********************")
        procedure = ZeroFieldSetupProcedure()
        procedure.set_setpoints_to_zero(0, 0, 0)
        # 2 second timer
        if procedure.check_if_stray_field_exist():
            print("Warning! Magnet Not in Range")
            # pylint: disable=E0602

        current_x, current_y, current_z, fields_x, fields_y, fields_z = procedure.get_correlated_current_and_fields(
            plot=True)

        calibration_coefficient_x, coefficient_of_determination_x = procedure.calculate_coefficient_and_r_squared(
            current_x, fields_x)
        calibration_coefficient_y, coefficient_of_determination_y = procedure.calculate_coefficient_and_r_squared(
            current_y, fields_y)
        calibration_coefficient_z, coefficient_of_determination_z = procedure.calculate_coefficient_and_r_squared(
            current_z, fields_z)

        print(
            "Calibration coefficient for X axis is {unknown}".format(
                unknown=calibration_coefficient_z))
        print("The coefficient of determination is {unknown}\n".format(
            unknown=coefficient_of_determination_x))

        print(
            "Calibration coefficient for Y axis is {unknown}".format(
                unknown=calibration_coefficient_y))
        print("The coefficient of determination is {unknown}\n".format(
            unknown=coefficient_of_determination_y))

        print(
            "Calibration coefficient for Z axis is {unknown}".format(
                unknown=calibration_coefficient_z))
        print("The coefficient of determination is {unknown}\n".format(
            unknown=coefficient_of_determination_z))

        if procedure.ask_user_to_continue() == "N":
            break

        RMS = procedure.calculate_noise(plot=True)
        print("RMS noise: {unknown}".format(unknown=RMS))

        if procedure.ask_user_to_continue() == "N":
            break

        update_offset()
        procedure.close_plot()
        break

    procedure.close_plot()
    print("Script Stopped")