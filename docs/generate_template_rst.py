import os


def main():
    """
    Generates a template rst file for use by sphinx auto documentation so we don't have to add new modules manually.
    """

    output_file = os.path.join(os.getcwd(), "shared_instrument_scripts.rst")
    text = generate_text()

    print("The following file text has been generated for {}".format(output_file))
    print(text)

    # Output to file
    with open(output_file, 'w') as f:
        f.writelines(text)


def generate_text():
    """
    Generates the text that will be written to the documentation template

    Returns: The text that will be written to file
    """
    cwd = os.getcwd()  # Should be docs folder
    text = ""

    try:
        # Run from parent dir where section folders are
        os.chdir("..")
        text = add_header(text)
        for section in ("general", "instrument", "technique"):
            text = add_section(section, text)
    except Exception as e:
        print("Unable to generate template, error was: {}".format(e))
        text = ""
    finally:
        # Restore to original dir before leaving
        os.chdir(cwd)

    return text


def add_header(current_text):
    """
    Adds a header to the current text that will be written to the template file.

    Args:
        current_text (string): The current text in the file

    Returns:
        A string of the new file contents
    """
    print("Adding header")
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
    """
    Adds the template automodule text for a module of a given name to a piece of text

    Args:
        name (string): Name of the module
        original_text (string): The starting text that the new text will be added to

    Returns:
        A copy of the original_text with the new automodule template text appended
    """
    print("Adding automodule text for {}".format(name))
    automodule_text = """
.. automodule:: {}
    :members:
    """.format(name)
    return original_text + os.linesep + automodule_text + os.linesep


def add_module(name, path, original_text):
    """
    Recursively add the automodule documentation for python files in the current and sub directories.

    Args:
        name: The name of the module
        path: The path to the module
        original_text: The starting text that the new text will be added to

    Return:
        A copy of the original text with the automodule documentation for the current module appended
    """
    print("Adding module text for {}".format(name))

    cwd = os.getcwd()  # So we can get back to where we started
    os.chdir(path)
    new_text = original_text

    def is_file_for_documentation(f):
        return os.path.isfile(os.path.join(path, f)) and not f.startswith("_") and os.path.splitext(f)[1] == ".py"

    # Add documentation for Python files in this dir
    for file_name in (o for o in os.listdir(path) if is_file_for_documentation(o)):
        new_text = add_automodule_entry(name + "." + os.path.splitext(file_name)[0], new_text)

    # Recursively at documentation for Python files in subdirs
    for subdir_name, subdir_path in ((o, os.path.join(path, o)) for o in os.listdir(path)
                                     if os.path.isdir(os.path.join(path, o))):
        try:
            new_text = add_module(name + "." + subdir_name, subdir_path, new_text)
        except Exception as e:
            print("Failed to add template documentation for module {}, error: {}".format(name, e))
        finally:
            os.chdir(path)

    os.chdir(cwd)
    return new_text


def add_section(name, original_text):
    print("Adding section text for {}".format(name))
    new_text = original_text + os.linesep + name.title() + os.linesep + "-"*len(name) + os.linesep

    # Add automodule text for this and each subdir recursively
    return add_module(name, os.path.join(os.getcwd(), name), new_text)


if __name__ == "__main__":
    main()
