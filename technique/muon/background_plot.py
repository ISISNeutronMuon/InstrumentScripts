"""
Create a background plot. Which is a matplotlib figure that runs on the secondary plot
"""
import os
import matplotlib
matplotlib.use('module://genie_python.matplotlib_backend.ibex_websocket_backend')
matplotlib.rcParams["axes.formatter.useoffset"] = False

from datetime import datetime, timedelta

from genie_python.genie_dae import DAE_PVS_LOOKUP
from matplotlib import pyplot
from matplotlib.ticker import MaxNLocator
import matplotlib.dates as mdates
from random import randrange
from functools import partial
from genie_python import genie as g
from genie_python.genie_cachannel_wrapper import CaChannelWrapper, CaChannelException, UnableToConnectToPVException
from genie_python.matplotlib_backend.ibex_websocket_backend import set_up_plot_default, SECONDARY_WEB_PORT
from requests import head, ConnectionError
from time import sleep
import threading

# Default Figure name for the plot
DEFAULT_FIGURE_NAME = "Background Plot"

# The prefix for the block server
BLOCK_PREFIX = "CS:SB:"

# Name of file which data points are saved to
SAVE_FILE = os.path.join(r"C:\\", "Instrument", "var", "tmp", "background_plot_data_{ioc_number:02d}.csv")


class BackgroundPlot(threading.Thread):
    """
    Create a background plot of some points which update
    """

    def __init__(self, interval, figure_name=DEFAULT_FIGURE_NAME, ioc_number=None):
        if ioc_number is None:
            raise ValueError("IOC number must be set")

        set_up_plot_default(is_primary=False, should_open_ibex_window_on_show=False)

        # x data for the plot, date time objects
        self.data_x = None
        # point data dictionary of arrays for each point
        self.data = None

        # matplotlib lines on plot
        self.lines = []

        # matplotlib figure
        self.figure = None

        # axis label for the y axis
        self.label_y_axis = "Values"

        self._interval = interval
        self.thread = None

        self._save_file = SAVE_FILE.format(ioc_number=ioc_number)
        self._figure_name = figure_name

    def start(self):
        """
        Start the back ground plot in a new thread

        Returns
        -------
        self
        """
        try:
            head("http://localhost:{}".format(SECONDARY_WEB_PORT))
            print("Background Plot: new plot not started because it is already running")
            return
        except ConnectionError:
            pass

        if pyplot.fignum_exists(self._figure_name):
            print("Figure already exists!")
            return

        self.figure = pyplot.figure(self._figure_name)

        self._first_point()
        labels = self.get_data_set_labels()
        for data_set, label in zip(self.data, labels):
            line, = pyplot.plot_date(self.data_x, data_set, '-', label=label)
            self.lines.append(line)

        self.set_up_plot()

        if self.saved_data_matches_current_dataset():
            self.load_data_from_save()
        else:
            self.start_new_data_file()

        pyplot.show()
        pyplot.ion()
        print("Background plot: Started")

        while True:
            try:
                self.update()
            except Exception as ex:
                print("Update plot failed with {}".format(ex))
            sleep(self._interval)
            pyplot.show()

    def set_up_plot(self):
        """
        Do any initial figure setup on start of plotting
        """
        pass

    def _first_point(self):
        """
        Get back the first point and set up initial data fields
        """
        attempt = 0
        self.data = None
        while self.data is None:
            first_point = self.get_data_point()
            try:
                if len(first_point) < 2:
                    raise TypeError
            except TypeError:
                raise TypeError("Error in plot: get_data_point() must return a list of at least two entries.")
            self.data_x = [first_point[0], ]
            if all([point is None for point in first_point[1:]]):
                self.data = None
                if attempt % 10 == 0:
                    print("background Plot: Can not read initial point")
                attempt += 1
            else:
                self.data = []
                for point in first_point[1:]:
                    self.data.append([point, ])

    def load_data_from_save(self):
        """
        Imports data from the save file
        """
        # Copy nested list structure from first point
        # Each list will contain data for one axis (a 'dataset')
        loaded_data = [list() for _ in range(len(self.data))]
        loaded_data_x = []

        with open(self._save_file, 'r') as csvfile:
            # Ignore header lines starting with #
            file_without_header = filter(lambda row: row if not row.startswith('#') else '', csvfile)

            data_point_err = []
            for row in file_without_header:
                row = row.split(",")
                # CSV format is timestamp in first column, then data columns
                try:
                    timestamp = row[0]
                    data_points_in_row = row[1:]
                    loaded_data_x.append(datetime.fromisoformat(timestamp))
                except (IndexError, ValueError) as e:
                    print(f'WARNING - Save file may be corrupted: {e}')
                    continue

                # Split the data up so the nth point in the row gets appended to the nth list in loaded_data
                for dataset, restored_data_point in zip(loaded_data, data_points_in_row):
                    # Append the new data point from this row onto the correct dataset
                    if not restored_data_point or "None" in restored_data_point:
                        data_point = None
                    else:
                        try:
                            data_point = float(restored_data_point)
                        except ValueError:
                            data_point = None
                            data_point_err.append(restored_data_point)
                    dataset.append(data_point)

            if data_point_err:
                print(f'WARNING - Save file may be corrupted: {len(data_point_err)} data points could not be appended '
                      f'to the dataset: {data_point_err}')

        # Add the data points collected since class initialisation
        for dataset, first_point in zip(loaded_data, self.data):
            dataset.extend(first_point)
        loaded_data_x.extend(self.data_x)
        self.data = loaded_data
        self.data_x = loaded_data_x

    def update(self):
        """
        Update the plot with a data point and redraw the figure. used as the function in matplotlib's FuncAnimation.

        Parameters
        ----------

        Returns
        -------
            List of matplotlib artists
        """
        if self.should_clear_plot():
            self.clear_plot()
            self.start_new_data_file()
        else:
            self.update_data()

        return self.update_figure()

    def start_new_data_file(self):
        """
        Starts a new data file, or deletes old data and creates new file
        """
        open(self._save_file, 'w').close()

    def save_data_point(self, points):
        """
        Appends the temporary save file with the latest data points

        Args:
            points: list containing data points to save. First value is timestamp
        """

        with open(self._save_file, 'a') as csvfile:
            csvfile.write(",".join(str(x) for x in points) + "\n")

    def update_data(self):
        """
        Update the data for the plot. Can be overloaded.
        Default behaviour gets the next point from get_data-point and adds it to data and data_x.
        """
        point = self.get_data_point()
        self.save_data_point(point)
        self.data_x.append(point[0])
        for data_set, point in zip(self.data, point[1:]):
            data_set.append(point)

    def update_figure(self):
        """
        Update the figure with the new data. Data is in self.data and self.data_x. Lines to update are in self.lines.

        Returns
        -------
        Artists used to update the plot.

        """
        for data_set, line in zip(self.data, self.lines):
            line.set_data(self.data_x, data_set)
        self.figure.gca().relim()
        additional_to_right = (self.data_x[-1] - self.data_x[0])/20
        self.figure.gca().set_xlim(left=self.data_x[0], right=self.data_x[-1] + additional_to_right)
        self.figure.gca().axes.xaxis.set_major_locator(MaxNLocator(5))
        self.figure.gca().axes.xaxis.set_major_formatter(mdates.DateFormatter("%d-%m-%y %H:%M"))
        self.figure.gca().axes.xaxis.set_tick_params(bottom=0.2, rotation=10)
        self.figure.gca().autoscale_view()
        return self.lines

    def get_data_point(self):
        """
        Get a single data point.

        Returns
        -------
        list of points the time followed by 1 data point per line
        """
        return datetime.now(), randrange(0, 50), randrange(25, 75), randrange(50, 100)

    def get_data_set_labels(self):
        """
        Get the labels for the lines in the data

        Returns
        -------
        label to be shown on a legend for each line of data
        """
        return ["set {}".format(i+1) for i in range(len(self.data))]

    def should_clear_plot(self):
        """
        True if the plot should be cleared otherwise False

        Should be overloaded for different desired behaviour.

        Returns
        -------
        False, the plot is never cleared
        """
        return False

    def saved_data_matches_current_dataset(self):
        """
        True if the saved dataset dimensions match, else False

        Should be overloaded for desired behaviour

        Returns
        -------
        False, data is never loaded from disc
        """
        return False

    def clear_plot(self):
        """
        Clear the plot by adding the first point and updating the figure

        Returns
        -------

        """
        self._first_point()
        self.update_figure()


class BackgroundBlockPlot(BackgroundPlot):
    """
    Background plot which plots a number of blocks. Clears the plot on the start of a new run

    Example
    -------

    Add the following line to your init

    >>> background_plot=BackgroundBlockPlot((("Temp_Sample", "value"), ("Temp_SP", "setpoint")), "Temperature").start()

    This will create a background plot for the Temp_Sample block and Temp_SP block with legend labels value and setpoint
    . The name of the plot and the y axis will be Temperature. It defaults to an interval of 0.5s

    >>> background_plot=BackgroundBlockPlot((("Temp_Sample", "value"),
                                             ("Temp_SP", "setpoint"),
                                             ("Result", "result")), "Temperature", interval=1).start()

    In this example we create a three line plot of Temp_Sample, Temp_SP and Result. The delay between samples is 1s.
    """

    def __init__(self, block_and_name_list, y_axis_label, ioc_number=1, interval=0.5):
        """
        Initialisation.

        Parameters
        ----------
        block_and_name_list: list[tuple(str, str)]
            List of blocks and their names on the legend

        y_axis_label: str
            y axis label

        interval: float
            interval at which block should be plotted in seconds

        ioc_number: int
            The number of the BGRSCRPT IOC which has spawned this class.
        """
        super(BackgroundBlockPlot, self).__init__(interval, "{} Plot".format(y_axis_label), ioc_number=ioc_number)
        self._run_state_pv = g.prefix_pv_name(DAE_PVS_LOOKUP["runstate"])
        self._run_number_pv = g.prefix_pv_name(DAE_PVS_LOOKUP["runnumber"])
        self._pv_names = []
        self._legend_labels = []
        for block, name in block_and_name_list:
            self._legend_labels.append(name)
            pv_name = g.prefix_pv_name("{}{}".format(BLOCK_PREFIX, block))
            self._pv_names.append(pv_name)

        self.y_axis_label = y_axis_label
        self.current_run_number = None

    def _get_pv_with_timeout(self, pv_name, to_string=False):
        """
        Get the value of a pv with a short timeout.

        This stops the graph from stuttering which it will do if using a longer timeout or the default genie_python
        get_pv implementation

        Parameters
        ----------
        pv_name:
            name of pv value to get
        to_string:
            whether to return the value as a string

        Returns
        -------
            pv's value
        """

        return CaChannelWrapper.get_pv_value(pv_name, timeout=self._interval / 4.0, to_string=to_string)

    def _get_pv_none_on_invalid_alarm(self, pv_name):
        """
        Get a pv value but return none if it is invalid alarm

        Parameters
        ----------
        pv_name:
            name of the pv to read

        Returns
        -------
            value or None is disconnected or in INVALID alarm
        """
        try:
            data = self._get_pv_with_timeout(pv_name)
            error = self._get_pv_with_timeout(pv_name + ".SEVR")
            if error == "INVALID":
                data = None
        except (CaChannelException, UnableToConnectToPVException):
            data = None
        return data

    def set_up_plot(self):
        """
        Do any initial figure setup on start of plotting. Draw legend and label axes
        """
        pyplot.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
                      ncol=min(3, len(self.data)), mode="expand", borderaxespad=0.)
        self.figure.gca().set_xlabel("Time")
        self.figure.gca().set_ylabel(self.y_axis_label)
        self.current_run_number = g.get_runnumber()

    def get_data_point(self):
        """
        Get the data point for the pv

        Returns
        -------
        time, block value, block setpoint
        """
        data = [self._get_pv_none_on_invalid_alarm(pv_name) for pv_name in self._pv_names]

        return [datetime.now()] + data

    def should_clear_plot(self):
        """
        Returns True if a new run has become since the last point was plotted

        Returns
        -------
        True when plot should be cleared, False otherwise
        """
        try:
            num = self._get_pv_with_timeout(self._run_number_pv)

            if num != self.current_run_number:
                run_state = self._get_pv_with_timeout(self._run_state_pv, to_string=True)
                if run_state == 'RUNNING':
                    self.current_run_number = num
                    return True
            return False
        except (CaChannelException, UnableToConnectToPVException):
            return False

    def get_data_set_labels(self):
        """
        Legend labels

        Returns
        -------
        Legend labels
        """
        return self._legend_labels

    def saved_data_matches_current_dataset(self):
        """
        Returns True if the saved dataset has same run number and number of variables as current dataset
        """

        # Dimensions of current data are (number of variables + 1 time dimension)
        current_dataset_dims = len(self.data) + 1

        try:
            saved_run_number, saved_dataset_dims = self._read_header()

            # Check the parameters in file match current dataset
            try:
                run_numbers_match = int(saved_run_number) == int(self.current_run_number)
            except ValueError as e:
                print(f'ValueError: {e}. run_numbers_match set to False.')
                run_numbers_match = False

            data_dimensions_match = saved_dataset_dims == current_dataset_dims
        except FileNotFoundError:
            valid_file_found = False
        else:
            valid_file_found = True

        if valid_file_found and run_numbers_match and data_dimensions_match:
            print("Dataset matches - loading values from save")
            dataset_matches = True
        elif valid_file_found:
            print("Dataset doesn't match - do not load from save")
            dataset_matches = False
        else:
            print("No valid save file found")
            dataset_matches = False

        return dataset_matches

    def _read_header(self):
        """
        Strips the usable information from the save file header
        """
        with open(self._save_file, "r") as csvfile:
            run_number_line = csvfile.readline()
            # Second line is for human readability, skip
            _ = csvfile.readline()
            sample_data_row = csvfile.readline()

        # Strip text from run number, must match header in start_new_data_file
        saved_run_number = run_number_line.replace("# run_number:", "")

        # Count number of columns in data row
        dimensions_in_saved_dataset = len(sample_data_row.split(","))

        return saved_run_number, dimensions_in_saved_dataset

    def start_new_data_file(self):
        """
        Starts a new data file with custom header
        """
        print('Start new data file with custom header')
        with open(self._save_file, 'w') as csvfile:
            csvfile.write("# run_number:{}\n".format(self.current_run_number))
            # Save axis names for human readability
            csvfile.write("# Axes: time, {}\n".format(', '.join(self.get_data_set_labels())))
