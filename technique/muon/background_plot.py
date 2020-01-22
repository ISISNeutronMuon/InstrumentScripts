"""
Create a background plot. Which is a matplotlib figure that runs in the background
"""
from datetime import datetime, timedelta
from threading import Thread

from genie_python.genie_dae import DAE_PVS_LOOKUP
from matplotlib import pyplot
from matplotlib.animation import FuncAnimation
from random import randrange
from functools import partial
from genie_python import genie as g
from genie_python.genie_cachannel_wrapper import CaChannelWrapper, CaChannelException, UnableToConnectToPVException
from requests import head, ConnectionError

# Default Figure name for the plot
DEFAULT_FIGURE_NAME = "Background Plot"


class BackgroundPlot(object):
    """
    Create a background plot of some points which update
    """

    def __init__(self, interval, figure_name=DEFAULT_FIGURE_NAME):
        # Animation object which updates the plot
        self._animation = None
        # x daa for the plot, date time objects
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

        self._figure_name = figure_name

    def start(self):
        """
        Start the back ground plot in a new thread

        Returns
        -------
        self
        """
        try:
            head("http://localhost:8988")
            print("Background Plot: new plot not started because it is already running")
            return
        except ConnectionError:
            pass

        self.thread = Thread(target=self._start_plot)
        self.thread.daemon = True
        self.thread.start()
        return self

    def _start_plot(self):
        """
        Start animation to plot the data in a new Thread
        """
    
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

        self._animation = FuncAnimation(self.figure, partial(self._update, self), interval=self._interval*1000)

        pyplot.show()

        print("Background plot: Started")

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

    def _update(self, frame, *fargs):
        """
        Update the plot, call update but catches any exceptions and prints them for the user to see

        Parameters
        ----------
        frame: int
            frame number of the animation (not typically needed)
        *fargs:
            any user arguments that should be passed to the animation
        """
        try:
            self.update(frame, *fargs)
        except Exception as ex:
            print("Update plot failed with {}".format(ex))

    def update(self, frame, *fargs):
        """
        Update the plot with a data point and redraw the figure. used as the function in matplotlib's FuncAnimation.

        Parameters
        ----------
        frame: int
            frame of the animation to plot
        fargs:
            other argument from the user (usually empty)

        Returns
        -------
            List of matplotlib artists
        """
        if self.should_clear_plot():
            self.clear_plot()
        else:
            self.update_data()

        return self.update_figure()

    def update_data(self):
        """
        Update the data for the plot. Can be overloaded.
        Default behaviour gets the next point from get_data-point and adds it to data and data_x.
        """
        point = self.get_data_point()
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
        self.figure.gca().set_xlim(left=self.data_x[0], right=self.data_x[-1] + timedelta(seconds=0.5))
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
    Background plot which plots a block, both value and setpoint. Clears the plot on the start of a new run

    Example
    -------

    Add the following line to your init

    background_plot=BackgroundBlockPlot("Sample_Temperature", "Temperature").start()

    This will create a background plot for the Sample_Temperature block for both set point and value with temperature
    as the name of the plot and the y axis. It defaults to an interval of 0.5s
    """

    def __init__(self, block_name, y_axis_label, interval=0.5):
        """
        Initialisation.

        Parameters
        ----------
        block_name: str
            Name of block to plot

        y_axis_label: str
            y axis label

        interval: float
            interval at which block should be plotted in seconds
        """
        super(BackgroundBlockPlot, self).__init__(interval, "{} Plot".format(y_axis_label))
        self._run_state_pv = g.prefix_pv_name(DAE_PVS_LOOKUP["runstate"])
        self._run_number_pv = g.prefix_pv_name(DAE_PVS_LOOKUP["runnumber"])
        self._pv_name = g.adv.get_pv_from_block(block_name)
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
        data = self._get_pv_none_on_invalid_alarm(self._pv_name)
        sp = self._get_pv_none_on_invalid_alarm("{}:SP".format(self._pv_name))

        return datetime.now(), data, sp

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
        Value and setpoint labels
        """
        return "value", "set point"
