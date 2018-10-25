Contributing to the shared GENIE-Python Scripts
===============================================

If you've written a module that has been useful on your beam-line, it
may be useful on other instruments.  We want to encourage new code
being added to the repository, but we must also ensure that everything
in the repository is reliable.  To this end, there are a couple of
recommended practices that all contributions should engage in before
submitting back to the master branch.

Testing
-------

Writing test code for a module guarantees that the code that is
working today will work tomorrow.  Changes that cause previously
working code to fail can be detected by the continuous integration
server and prevented from being pushed into the production environment
on the beam-lines.

Currently, the python unittest module is being used for test discovery
and orchestration.  To add tests to your module.

1. Add a test sub-folder to your module folder
2. Add an __init__.py file to the test sub-folder
3. Add the test files to the test folder.  Each test file should have
   a name that starts with "test_"
4. Add the tests to the test files
5. In the root directory, run ``python -m unittest discover`` and
   check that your tests have been run.

As a matter of style, we recommend using the doctest module to create
tests.  This module runs through the examples in your documentation
and ensure that the examples run as given.  This both encourages the
writing of thorough documentation and prevents the documentation from
becoming out of date.

It is also worth noting that the continuous integration server runs
its tests on python version 2.7 and 3.6.  This ensures that all code
will remain forward compatible when Python 2 stops being maintained
in 2020.  This does create some small hassle now to support both
versions, but it will save a massive effort down the road to test and
cheap the whole library for errors during the upgrade.

Documenting
-----------

Each new module should add a sub-directory to ``doc/source`` which will
contain the documentation for that module.  The index for that
documentation should then be added to the table of contents for the
root ``index.rst``.  Finally, the individual code modules should be
added to ``reference.rst``.


Style
-----

To improve readability and prevent bugs, Python coding style is
enforced via the ``pylint`` and ``pyflakes`` programs.  Code that does
not conform cannot be merged into the mainline.  Note that it *is*
acceptable to temporarily turn off a warning for a specific line in a
source file if there is a particular reason to bypass the warning.
The main goal is to make writing good code the path of least
resistance, not to enforce a dogmatic adherence to coding standards.

There is already a .pylintrc file that make some modifications to the
coding standards.  Changes to this file should not be taken likely and
will need review by multiple parties.
