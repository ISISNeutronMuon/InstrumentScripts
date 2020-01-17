from genie_python import genie as g
import time
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from builtins import range
from builtins import input
import sys

PV_AUTO_FEEDBACK_MODE = "ZFCNTRL_01:AUTOFEEDBACK"
PV_READ_MAGNETIC_FIELD_STRENGTH = "ZFMAGFLD_01:FIELDSTRENGTH"
PV_FIELD_SETPOINT = "ZFCNTRL_01:FIELD:{}:SP"
PV_CORRECTED_FIELD = "ZFCNTRL_01:FIELD:{}"
PV_RAW_MEASUREMENT = "ZFCNTRL_01:FIELD:{}:MEAS"
PV_OFFSET = "ZFMAGFLD_01:{}:OFFSET"
PV_POWER_SUPPLY_UPPER_LIMIT = "ZFCNTRL_01:OUTPUT:{}:CURR:SP.DRVH"
PV_POWER_SUPPLY_LOWER_LIMIT = "ZFCNTRL_01:OUTPUT:{}:CURR:SP.DRVL"
PV_POWER_SUPPLY_SET_POINT = "ZFCNTRL_01:OUTPUT:{}:CURR:SP"
AUTO_FEEDBACK_MODE = 1
MANUAL_MODE = 0


class ZeroFieldSetupProcedure():
    # pylint: disable=W0232
    """
    Class for setting up zero field procedure. Contains all the required function which can be run sequentially to
    to complete the set up
    """

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
        return g.get_pv(PV_READ_MAGNETIC_FIELD_STRENGTH)

    def set_fields_setpoint_to_zero(self):
        """
        Set all set points to 0
        :param value_x: target value for x axis
        :param value_y: target value for y axis
        :param value_z: target value for z axis
        :return: None
        """
        g.set_pv(PV_FIELD_SETPOINT.format("X"), 0, is_local=True)
        g.set_pv(PV_FIELD_SETPOINT.format("Y"), 0, is_local=True)
        g.set_pv(PV_FIELD_SETPOINT.format("Z"), 0, is_local=True)

    def get_correlated_current_and_fields(self, plot=False):
        """
        Gets correlated current and corrected fields, 2 second wait before taking the field
        reading in all three axis
        :param plot: data to be plotted or not
        :return: correlated current and fields for each axis
        """
        ps_lower_limit_x = g.get_pv(PV_POWER_SUPPLY_LOWER_LIMIT.format("X"), is_local=True)
        ps_lower_limit_y = g.get_pv(PV_POWER_SUPPLY_LOWER_LIMIT.format("Y"), is_local=True)
        ps_lower_limit_z = g.get_pv(PV_POWER_SUPPLY_LOWER_LIMIT.format("Z"), is_local=True)

        ps_max_x = abs(g.get_pv(PV_POWER_SUPPLY_UPPER_LIMIT.format("X"), is_local=True) - \
                   ps_lower_limit_x)

        ps_max_y = abs(g.get_pv(PV_POWER_SUPPLY_UPPER_LIMIT.format("Y"), is_local=True) - \
                   ps_lower_limit_y)

        ps_max_z = abs(g.get_pv(PV_POWER_SUPPLY_UPPER_LIMIT.format("Z"), is_local=True) - \
                   ps_lower_limit_z)

        scale_x = ps_max_x / 20
        scale_y = ps_max_y / 20
        scale_z = ps_max_z / 20

        current_x = []
        current_y = []
        current_z = []

        fields_x = []
        fields_y = []
        fields_z = []

        print("Setting current and reading fields ...")
        # 21 evenly spaced steps
        for x in range(21):
            current_x.append(ps_lower_limit_x + (x * scale_x))
            current_y.append(ps_lower_limit_y + (x * scale_y))
            current_z.append(ps_lower_limit_z + (x * scale_z))
			
            print("Setting power supply set point to {} ...".format(ps_lower_limit_x + (x * scale_x)))
            g.set_pv(PV_POWER_SUPPLY_SET_POINT.format("X"), ps_lower_limit_x + (x * scale_x), is_local=True)
            g.set_pv(PV_POWER_SUPPLY_SET_POINT.format("Y"), ps_lower_limit_y + (x * scale_y), is_local=True)
            g.set_pv(PV_POWER_SUPPLY_SET_POINT.format("Z"), ps_lower_limit_z + (x * scale_z), is_local=True)
            time.sleep(2)

            fields_x.append(self.get_single_corrected_field_value("X"))
            fields_y.append(self.get_single_corrected_field_value("Y"))
            fields_z.append(self.get_single_corrected_field_value("Z"))

        self.put_power_supply_in_middle()

        if plot is True:
            self.plot_field_against_current(current_x, fields_x, "Field X")
            self.plot_field_against_current(current_y, fields_y, "Field Y")
            self.plot_field_against_current(current_z, fields_z, "Field Z")

        return current_x, current_y, current_z, fields_x, fields_y, fields_z

    def put_power_supply_in_middle(self):
        mid_val_x = (g.get_pv(PV_POWER_SUPPLY_UPPER_LIMIT.format("X")) +
                     g.get_pv(PV_POWER_SUPPLY_LOWER_LIMIT.format("X"))) / 2

        mid_val_y = (g.get_pv(PV_POWER_SUPPLY_UPPER_LIMIT.format("Y")) +
                     g.get_pv(PV_POWER_SUPPLY_LOWER_LIMIT.format("Y"))) / 2

        mid_val_z = (g.get_pv(PV_POWER_SUPPLY_UPPER_LIMIT.format("Z")) +
                     g.get_pv(PV_POWER_SUPPLY_LOWER_LIMIT.format("Z"))) / 2

        g.set_pv(PV_POWER_SUPPLY_SET_POINT.format("X"), mid_val_x, is_local=True)
        g.set_pv(PV_POWER_SUPPLY_SET_POINT.format("Y"), mid_val_y, is_local=True)
        g.set_pv(PV_POWER_SUPPLY_SET_POINT.format("Z"), mid_val_z, is_local=True)


    def plot_field_against_current(self, current, field, label):
        fig = plt.figure(figsize=(8,5))
        fig.set_size_inches(8,8)
        fig.suptitle("Plot of Current and Field")
        plt.tick_params(axis="x", pad=10)
        plt.scatter(current, field)
        plt.plot(current, field, label=label)
        plt.xticks(current)
        plt.xlabel("Current (A)")
        plt.ylabel("Field (mG)")
        plt.legend(loc="upper left")
        plt.show()

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

    def calculate_noise(self, mode, plot=False):
        """
        Calculates the noise in each axis over 20 seconds
        :param plot: data to be plotted or not
        :return: RMS noise value
        """
        g.set_pv(PV_AUTO_FEEDBACK_MODE, mode, is_local=True)
        if (mode == AUTO_FEEDBACK_MODE):
            time.sleep(6)
        else:
            # manual mode
            time.sleep(3)

        number_of_readings = 20

        fields_x = []
        fields_y = []
        fields_z = []

        print("Reading fields over 20 second period...\n")
        # 20 readings, one second apart
        for x in range(number_of_readings):

            fields_x.append(self.get_single_corrected_field_value("X"))
            fields_y.append(self.get_single_corrected_field_value("Y"))
            fields_z.append(self.get_single_corrected_field_value("Z"))
            sys.stdout.write("*")
            sys.stdout.flush()
            time.sleep(1)
        print("\n")

        # calculating variance of each field
        var_x = np.var(fields_x)
        var_y = np.var(fields_y)
        var_z = np.var(fields_z)

        rms = np.sqrt((var_x + var_y + var_z))

        if plot is True:
            fig = plt.figure()
            plt.plot([x for x in range(number_of_readings)], fields_x, color="red", label="field X", marker="o")
            plt.plot([x for x in range(number_of_readings)], fields_y, color="green", label="field Y", marker="o")
            plt.plot([x for x in range(number_of_readings)], fields_z, color="blue", label="field Z", marker="o")
            plt.xticks([x for x in range(number_of_readings)])
            fig.suptitle("AUTO FEEDBACK" if mode == AUTO_FEEDBACK_MODE else "MANUAL")
            plt.xlabel("Time (sec)")
            plt.ylabel("Field (mG)")
            plt.legend(loc="upper left")
            plt.show()

        return rms

    def check_stray_field(self, val):
        if (val < 4000):
            return val

    def check_magnet_in_range(self):
        """
        Check if there is huge stray field
        :return: True if there is huge stray field
        """
        magnet_in_range = True
        for direction in ["X", "Y", "Z"]:
            corrected_field_value = self.get_single_corrected_field_value(direction)
            if corrected_field_value > 4000:
                print("Stray field of {} in {} axis".format(corrected_field_value, direction))
                magnet_in_range = False

        return magnet_in_range

    def ask_user_to_continue(self):
        """
        Ask user if they want to continue further
        :return: True if user want to continue or False if they do not want to continue
        """
        reply = ""
        while reply.lower() != "y" and reply.lower() != "n":
            reply = input("Would you like to continue? Y/N\n")
        if reply.lower() == "n":
            return False
        return True

    def get_single_corrected_field_value(self, field_direction):
        """
        get single corrected field value
        :param field_direction: X, Y or Z
        :return: corrected field value from the given direction
        """
        return g.get_pv(
            PV_CORRECTED_FIELD.format(field_direction), is_local=True)


def update_offset():
    """
    updates the offset so that the corrected field reading is 0 for each axis
    :return: None
    """

    for direction in ["X", "Y", "Z"]:
        raw_measurement = g.get_pv(PV_RAW_MEASUREMENT.format(direction), is_local=True)
        new_offset = raw_measurement - 0
        g.set_pv(PV_OFFSET.format(direction), new_offset, is_local=True)


def run_zero_field_set_up():
    """
    Run all the functions in order for set up
    :return:
    """
    # set to manual initially
    g.set_pv(PV_AUTO_FEEDBACK_MODE, MANUAL_MODE, is_local=True)

    print("***********************")
    procedure = ZeroFieldSetupProcedure()
    procedure.set_fields_setpoint_to_zero()
    print("Checking if magnet is in range\n")
    # 2 second timer
    time.sleep(2)
    if procedure.check_magnet_in_range() is False:
        return

    current = 0
    field = 1
    axis = 2

    current_x, current_y, current_z, fields_x, fields_y, fields_z = procedure.get_correlated_current_and_fields(
        plot=True)

    for x in [[current_x, fields_x, "X"], [current_y, fields_y, "Y"], [current_z, fields_z, "Z"]]:
        calibration_coefficient, coefficient_of_determination = procedure.calculate_coefficient_and_r_squared(
            x[current], x[field])
        print("Calibration coefficient for {} axis is {} mG/A".format(x[axis], calibration_coefficient))

        if (calibration_coefficient != 0):
            print ("{} A/mG({})".format(1/calibration_coefficient, x[axis]))

        print("The coefficient of determination is {}\n".format(coefficient_of_determination))

    if procedure.ask_user_to_continue() == False:
        return

    procedure.set_fields_setpoint_to_zero()
    print("RMS noise for auto-feedback mode is: {}".format(procedure.calculate_noise(AUTO_FEEDBACK_MODE, plot=True)))

    procedure.set_fields_setpoint_to_zero()
    print("RMS noise for manual mode is: {}".format(procedure.calculate_noise(MANUAL_MODE, plot=True)))
    return
