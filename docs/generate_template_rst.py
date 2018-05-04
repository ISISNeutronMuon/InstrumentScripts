import os

def main():
    """
    Generates a template rst file for use by sphinx auto documenation so we don't have to add new modules manually
    """
    cwd = os.getcwd()
    os.chdir("..")
    text = ""
    text = add_header(text)
    text = add_section("general", text)
    text = add_section("instrument", text)
    text = add_section("technique", text)
    os.chdir(cwd)

    output_file = os.path.join(cwd, "shared_instrument_scripts.rst")
    print("The following file text has been generated for {}".format(output_file))
    print(text)

    # Output to file
    with open(output_file, 'w') as f:
        f.writelines(text)


def add_header(current_text):
    """
    Adds a header to the current text that will be written to the template file.

    Args:
        current_text (string): The current text in the file

    Returns:
        A string of the new file contents
    """
    print("Writing header")
    header_text = """

.. shared_instrument_scripts documentation master file
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to the ISIS shared Python scripting documentation!
==========================================================

.. toctree::
   :maxdepth: 2

    """
    return current_text + header_text


def add_automodule_entry(name, original_text):
    print("Adding automodule text for {}".format(name))
    automodule_text = """
.. automodule:: {}
    :members:
    """.format(name)
    return original_text + os.linesep + automodule_text + os.linesep

def add_module(name, original_text):
    print("Adding module text for {}".format(name))
    new_text = original_text

    cwd = os.getcwd()
    for file_name in (o for o in os.listdir(cwd) if os.path.isfile(os.path.join(cwd,o)) and not o.startswith("_")):
        new_text = add_automodule_entry(name + "." + os.path.splitext(file_name)[0], new_text)

    for subdir_name, subdir_path in ((o, os.path.join(cwd, o)) for o in os.listdir(cwd)
                                     if os.path.isdir(os.path.join(cwd,o))):
        os.chdir(subdir_path)
        new_text = add_module(name + "." + subdir_name, new_text)
        os.chdir(cwd)

    return new_text


def add_section(name, original_text):
    print("Adding section text for {}".format(name))
    new_text = original_text

    # Add section header
    new_text += os.linesep + name.title() + os.linesep + "-"*len(name) + os.linesep

    # Add automodule for each file recursively
    cwd = os.getcwd()
    os.chdir(os.path.join(cwd, name))
    new_text = add_module(name, new_text)
    os.chdir(cwd)

    return new_text


if __name__ == "__main__":
    main()