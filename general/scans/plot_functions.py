"""
Functions and utilities for plotting.
"""

import matplotlib.pyplot as plt
import numpy as np
from general.scans.monoid import MonoidList

# Min and max on graph if there are no points
DEFAULT_FRACTION_SPACING_TO_ADD = 0.05
NO_POINTS_MAX_Y = 0.05
NO_POINTS_MIN_Y = -0.05

# Range if min or max is infinite, if both infinite taken from 0
INF_POINT_MIN_Y = -1
INF_POINT_MAX_Y = 1


class PlotFunctions:
    """
    Encapsulate some of the interactions and setting for creating matplotlib graphs
    """

    def __init__(self, data_marker_size=3, markers="dosp+xv^<>", color_cycle=None, fit_colour="orange"):
        """
        Initialise plot functions with defaults plotting

        Parameters
        ----------
        data_marker_size
            size of the marker
        markers
            list of markers to use in order
        color_cycle
            list of colours to use
        fit_colour
            colour for a fit to the data
        """
        self.data_marker_size = data_marker_size
        if color_cycle is None:
            try:
                self.color_cycle = plt.rcParams["axes.prop_cycle"].by_key()["color"]
            except KeyError:
                self.color_cycle = ["k", "b", "g", "r"]
        else:
            self.color_cycle = color_cycle
        self.data_markers = markers
        self.fit_colour = fit_colour

        self._fig = None
        self._axis = None

    def set_figure_and_axis(self, figure, axis):
        """
        Set the matplotlib figure and axis

        Parameters
        ----------
        figure
            figure to use
        axis
            axis to use
        """
        self._fig = figure
        self._axis = axis

    def plot_data_with_errors(self, xs, ys):
        """
        Plot an xy line with error bars

        Parameters
        ----------
        xs
            x coordinates list
        ys
            y values either a Monoid list or object with values and err attributes containing list of points

        """

        rng_min, rng_max = self._plot_range(ys)
        self._axis.set_ylim(rng_min, rng_max)

        if ys is not None and len(ys) > 0:
            if isinstance(ys[0], MonoidList):
                for y, err, color, marker in zip(ys.values(), ys.err(),
                                                 self.color_cycle, self.data_markers):
                    self._axis.errorbar(xs, y, yerr=err, fmt="", color=color,
                                        marker=marker, markersize=self.data_marker_size, linestyle="None")
            else:
                self._axis.errorbar(xs, ys.values(), yerr=ys.err(), color=self.color_cycle[0],
                                    marker=self.data_markers[0], markersize=self.data_marker_size)

    def _plot_range(self, points):
        """
        Calculate the plot range for the points.

        Parameters
        ----------
        points
            points of data as a numpy array

        Returns
        -------
        range as a tuple: min and max
        """
        if not points:
            return NO_POINTS_MIN_Y, NO_POINTS_MAX_Y

        low = points.min()
        high = points.max()
        if not np.isfinite(low) and not np.isfinite(high):
            return INF_POINT_MIN_Y, INF_POINT_MAX_Y
        if not np.isfinite(low):
            low = high + INF_POINT_MIN_Y
        if not np.isfinite(high):
            high = low + INF_POINT_MAX_Y

        return self._add_space_to_range(low, high)

    def _add_space_to_range(self, low, high, fraction_to_add=DEFAULT_FRACTION_SPACING_TO_ADD):
        """
        Add extra space to a range based on the size of the range
        Parameters
        ----------
        low
            low limit
        high
            high limit
        fraction_to_add
            fraction of range to add and subtract to limits

        Returns
        -------
            tuple of low and high limit
        """
        diff = high - low
        return low - fraction_to_add * diff, high + fraction_to_add * diff

    def setup_plot(self, x_min, x_max, x_label=None, x_unit=None, y_label=None, y_unit=None):
        """
        Set up the plot

        Parameters
        ----------
        x_min
            minimum x value
        x_max
            maximum x value
        x_label
            label for x axis
        x_unit
            unit for x axis
        y_label
            label for y axis
        y_unit
            unit of y axis
        """
        self._axis.clear()
        full_x_label = self._create_axis_title(x_label, x_unit)

        if full_x_label is not None:
            self._axis.set_xlabel(full_x_label)
            manager = plt.get_current_fig_manager()
            manager.set_window_title("Figure {}: {}".format(self._fig.number,  full_x_label))

        full_y_label = self._create_axis_title(y_label, y_unit)
        if full_y_label is not None:
            self._axis.set_ylabel(full_y_label)
        if isinstance(x_min, tuple):
            x_min = x_min[0]
            x_max = x_max[0]
        range_min, range_max = self._add_space_to_range(x_min, x_max)
        self._axis.set_xlim(range_min, range_max)

    def _create_axis_title(self, label, unit):
        """
        Create axis title

        Parameters
        ----------
        label
            label for axis; None for not provided
        unit
            unit for axis; None for not provided

        Returns
        -------
        Best axis label dependent on info e.g. label (unit) or unit or  None for nothing provided
        """
        full_label = None
        if label is not None and unit is not None:
            full_label = "{} ({})".format(label, unit)
        elif label is not None:
            full_label = label
        elif unit is not None:
            full_label = unit

        return full_label

    def draw(self):
        """
        Draw the plot.
        """
        plt.draw()

    def save(self, save):
        """
        Save plot to a file

        Parameters
        ----------
        save
            filename of the file to save the plot to; Nor a string don't save
        """
        if isinstance(save, str):
            self._fig.savefig(save)

    def plot_fit(self, plot_x, fit_y, fit_label):
        """
        Plot a fit line

        Parameters
        ----------
        plot_x
            x values
        fit_y
            y fit values
        fit_label
            label for the fit
        """
        self._axis.plot(plot_x, fit_y, "-", label=fit_label, color=self.fit_colour)
        self._axis.legend(bbox_to_anchor=(0, 1.02, 1, 0.2), loc="lower left", mode="expand", borderaxespad=0, ncol=3)

    def plot_vertical_fit_line(self, x_pos, fit_label):
        """
        Plot a fit line vertically

        Parameters
        ----------
        x_pos
            position to plot the line
        fit_label
            label for the fit line
        """
        self._axis.axvline(x=x_pos, color=self.fit_colour)
        self._axis.legend([fit_label], bbox_to_anchor=(0, 1.02, 1, 0.2), loc="lower left", mode="expand",
                          borderaxespad=0, ncol=3)
