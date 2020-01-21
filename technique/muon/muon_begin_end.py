from __future__ import print_function
from genie_python import genie as g
from six.moves import input


def get_input(prompt):
    """
    Get input from the user (allows us to mock more complex functions for testing than patching input).

    Parameters
    ----------
    prompt: str
      The string to prompt the user

    Returns
    -------
    str
      The user input
    """
    return input(prompt)


# The keys for parameters in the sample parameters dictionary
name_par = "NAME"
orient_par = "GEOMETRY"
temp_par = "TEMP_LABEL"
field_par = "FIELD_LABEL"
comment_par = "COMMENTS"
# The key for the geometry parameter in the beamline parameters dictionary
geometry_par = "GEOMETRY"


def set_name_sample_par(sample_pars):
    """
    Ask the user if the sample parameter (name) is correct and allow them to change it if not.

    Parameters
    ----------
    sample_pars: dict
        The sample parameters that is to contain the name parameter.
    """
    old_sample_name = sample_pars.get(name_par, "")
    new_sample = get_input("Sample [{}]?".format(old_sample_name))
    if new_sample != "":
        g.change_sample_par(name_par, new_sample)


def set_orient_sample_par(sample_pars):
    """
    Ask the user if the sample parameter (orientation) is correct and allow them to change it if not.

    Parameters
    ----------
    sample_pars: dict
        The sample parameters that is to contain the orientation parameter.
    """
    old_orientation = sample_pars.get(orient_par, "")
    new_orient = get_input("Orientation [{}]?".format(old_orientation))
    if new_orient != "":
        g.change_sample_par(orient_par, new_orient)


def set_temp_sample_par(sample_pars):
    """
    Ask the user if the sample parameter (temp) is correct and allow them to change it if not.

    Parameters
    ----------
    sample_pars: dict
        The sample parameters that is to contain the temp parameter.
    """
    old_temp = sample_pars.get(temp_par, "")
    new_temp = get_input("Temperature [{}]?".format(old_temp))
    if new_temp != "":
        g.change_sample_par(temp_par, new_temp)


def set_field_sample_par(sample_pars):
    """
    Ask the user if the sample parameter (field) is correct and allow them to change it if not.

    Parameters
    ----------
    sample_pars: dict
        The sample parameters that is to contain the field parameter.
    """
    old_field = sample_pars.get(field_par, "")
    new_field = get_input("Field [{}]?".format(old_field))
    if new_field != "":
        g.change_sample_par(field_par, new_field)


def set_geometry_beamline_par(beamline_pars):
    """
    Ask the user if the sample parameter (geometry) is correct and allow them to change it if not.

    Parameters
    ----------
    beamline_pars: dict
        The sample parameters that is to contain the geometry parameter.
    """
    old_geometry = beamline_pars.get(geometry_par, "")
    new_geometry = None
    while new_geometry not in {"", "L", "T"}:
        new_geometry = get_input("Geometry (L or T) [{}]?".format(old_geometry))
    if new_geometry != "":
        g.change_beamline_par(geometry_par, new_geometry)


def set_rb_num():
    """
    Ask the user if the rb number is correct and allow them to change it if not.
    """
    old_rb_num = g.get_rb()
    while True:
        new_rb_num = get_input("RBNo [{}]?".format(old_rb_num))
        if new_rb_num == "" or new_rb_num.isdigit():
            break
        else:
            print("RB number must be a number or blank to skip setting")
    if new_rb_num != "":
        g.change_rb(new_rb_num)


def set_users():
    """
    Ask the user if the users are correct and allow them to change it if not.
    """
    old_exp_team = g.get_users()
    new_exp_team = get_input("Experimental Team [{}]?".format(old_exp_team))
    if new_exp_team != "":
        g.change_users(new_exp_team)


def set_comments_sample_par(sample_pars):
    """
    Ask the user if the sample parameter (comments) is correct and allow them to change it if not.

    Parameters
    ----------
    sample_pars: dict
        The sample parameters that is to contain the comments parameter.
    """
    old_comments = sample_pars.get(comment_par, "")
    new_comments = get_input("Comment [{}]?".format(old_comments))
    if new_comments != "":
        g.change_sample_par(comment_par, new_comments)


def construct_title():
    """
    Construct a run title from the run information: sample name, temperature label and field label.

    Returns:
        str: run title
    """
    sample_pars = g.get_sample_pars()
    return "{}_{}_{}".format(sample_pars[name_par], sample_pars[temp_par], sample_pars[field_par])


def set_label(sample=True, orient=True, temp=True, field=True, geometry=True, rb_num=True, exp_team=True, comment=True):
    """
    Set the run information.

    Parameters
    ----------
    sample: bool
        Whether or not to change the name of the sample
    orient: bool
        Whether or not to change the sample parameter: orientation
    temp: bool
        Whether  or not to change the sample parameter: temperature
    field: bool
        Whether or not to change the sample parameter: field
    geometry: bool
        Whether ot not to change the beamline parameter: geometry
    rb_num: bool
        Whether or not to change the rb number
    exp_team: bool
        Whether or not to change the user
    comment: bool
        Whether or not to change the sample parameter: comments
    """
    sample_pars = g.get_sample_pars()
    if sample:
        set_name_sample_par(sample_pars)
    if orient:
        set_orient_sample_par(sample_pars)
    if temp:
        set_temp_sample_par(sample_pars)
    if field:
        set_field_sample_par(sample_pars)
    if geometry:
        beamline_pars = g.get_beamline_pars()
        set_geometry_beamline_par(beamline_pars)
    if rb_num:
        set_rb_num()
    if exp_team:
        set_users()
    if comment:
        set_comments_sample_par(sample_pars)
    new_title = construct_title()
    print("Run title = {}".format(new_title))
    g.change_title(new_title)


def begin_precmd(**pars):
    """
    Set the run information.

    Parameters
    ----------
    quiet: bool
      If true suppress run title question output
    """
    if not pars.get('quiet', False):
        set_label()


def show_label():
    """
    Print out the run information including the sample parameters (name, orientation, temperature, field, comments),
     the rb number, the users and the geometry beamline parameters.
    """
    sample_pars = g.get_sample_pars()
    beamline_pars = g.get_beamline_pars()
    if name_par in sample_pars:
        print("Sample = {}".format(sample_pars[name_par]))
    else:
        print("Sample not set in sample parameters")
    if orient_par in sample_pars:
        print("Orientation = {}".format(sample_pars[orient_par]))
    else:
        print("Orientation not set in sample parameters")
    if temp_par in sample_pars:
        print("Temp = {}".format(sample_pars[temp_par]))
    else:
        print("Temp not set in sample parameters")
    if field_par in sample_pars:
        print("Field = {}".format(sample_pars[field_par]))
    else:
        print("Field not set in sample parameters")
    if geometry_par in beamline_pars:
        print("Geometry = {}".format(beamline_pars[geometry_par]))
    else:
        print("Geometry not set in beamline parameters")
    print("RB Number = {}".format(g.get_rb()))
    print("Experimental Team = {}".format(g.get_users()))
    if comment_par in sample_pars:
        print("Comment = {}".format(sample_pars[comment_par]))
    else:
        print("Comment not set in sample parameters")
    print("Run title = {}".format(g.get_title()))


def end_precmd(**pars):
    """
    Just before ending the run check that the run information is correct.

    Parameters
    ----------
    quiet: bool
      If true suppress run title question output
    """

    if not pars.get('quiet', False):
        while True:
            print("Run information:\n")
            show_label()
            label_correct = get_input("Is the run information correct (y/n)?")
            if label_correct.lower() == "y":
                break
            else:
                set_label()
