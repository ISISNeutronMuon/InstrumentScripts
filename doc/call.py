#!/usr/bin/env python

import ast
import os
import sys

try:
    from functools import singledispatch
except ImportError:
    sys.exit()  # singledispatch is only in python 3


def valid_module(module):
    """Confirm that we're in one of the main modules"""
    return module.startswith("general") or module.startswith("technique") or \
        module.startswith("instrument")


def file_to_module(filename):
    """Turn a file name into a module name"""
    return filename[:-3].replace("/", ".")


def dir_to_module(filename):
    """Turn a directory name into a module"""
    return filename.replace("/", ".")


@singledispatch
def handle(x, filename):
    """Pull the module imports out of a node"""
    return []


@handle.register(ast.Import)
def _(x, filename):
    """Pull the module imports out of a node"""
    return [i.name for i in x.names if valid_module(i.name)]


@handle.register(ast.ImportFrom)
def _(x, filename):
    """Pull the module imports out of a node"""
    # print(dir(x))
    if valid_module(x.module) or x.level > 0:
        if x.level == 0:
            header = ""
        elif x.level == 1:
            header = dir_to_module(os.path.dirname(filename)) + "."
        else:
            header = os.path.relname(
                os.path.dirname(filename), "/".join([".." * (x.level-1)])) + "."
        return [header + x.module]
    return []


def load_file(filename):
    """Get the function calls from a module"""
    with open(filename, "r") as infile:
        data = infile.read()

    temp = ast.parse(data, filename)

    result = [
        sum([handle(node, filename) for node in ast.walk(part)], [])
        for part in temp.body]
    return (filename, sum(result, []))


def make_graphs(data):
    """Make a link from a location to the function called"""
    base = file_to_module(data[0])
    sources = data[1]
    lines = ['  "{}" -> "{}";'.format(base, source) for source in sources]
    return "\n".join(lines)


def make_node(module):
    """Create a node for a module"""
    style = " []"
    return '  "{}"{};'.format(module, style)


def make_cluster(name, color, modules):
    """Create a cluster of all of the functions in the given module"""
    header = '''subgraph "cluster_{name:}" {{
node [color={color:}];
color={color:};
label="{name:}";
'''.format(name=name, color=color)
    nodes = "\n".join([make_node(m) for m in modules if m.startswith(name)])
    footer = "\n}"
    return header+nodes+footer


NAMES = ["instrument.larmor", "instrument.zoom", "instrument.loq",
         "technique.sans", "general.scans"]
COLORS = ["blue", "red", "cyan", "black", "black"]


def make_dot(data):
    """Create a graph file of the function calls in the module"""
    data = list(data)
    modules = sum([d[1] for d in data], []) + [file_to_module(d[0])
                                               for d in data if d[1]]
    modules = [m for m in modules if "test" not in m]
    clusters = [make_cluster(name, color, modules)
                for (name, color) in zip(NAMES, COLORS)]
    return 'digraph G {{\nrankdir="LR";\n{}\n{}\n}}'.format(
        "\n".join(clusters),
        "\n\n".join([make_graphs(datum) for datum in data]))


dirs = ["general", "technique", "instrument"]

FILES = [
    os.path.join(directory, name)
    for d in dirs
    for (directory, _, names)
    in os.walk(os.path.relpath(os.path.join("..", d), ".."))
    for name in names
    if name[-3:] == ".py"]

print(make_dot(map(load_file, FILES)))
