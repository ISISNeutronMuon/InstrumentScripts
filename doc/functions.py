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
    return module.startswith("general") or m.startswith("technique") or m.startswith("instrument")


def file_to_module(filename):
    """Turn a file name into a module name"""
    return filename[:-3].replace("/", ".")


def dir_to_module(filename):
    """Turn a directory name into a module"""
    return filename.replace("/", ".")


@singledispatch
def names(x, filename):
    """Pull the function call names out of a node"""
    return []


@names.register(ast.FunctionDef)
def _(x, filename):
    """Pull the function call names out of a node"""
    subvalues = [calls(node, filename) for node in ast.walk(x)]
    return [(x.name, subvalues)]

def load_file(filename):
    with open(filename, "r") as infile:
        data = infile.read()

    temp = ast.parse(data, filename)

    result = [
        sum([names(node, filename) for node in ast.walk(part)], [])
        for part in temp.body]
    return (filename, sum(result, []))


@singledispatch
def calls(x, filename):
    """Return all of the function calls in a node"""
    return []


@calls.register(ast.Call)
def _(x, filename):
    """Return all of the function calls in a node"""
    if type(x) != ast.Call:
        return []
    if isinstance(x.func, ast.Name):
        return [x.func.id]
    if isinstance(x.func, ast.Attribute):
        return [x.func.attr]
    return [str(x.func)]


def make_graphs(data):
    """Made a link from the call site to the called function"""
    base = file_to_module(data[0])
    sources = data[1]
    lines = ['  "{}" -> "{}";'.format(base, source) for source in sources]
    return "\n".join(lines)


def make_cluster(name, calls, funcs, drawn):
    """Group together functions in the same module"""
    header = ('subgraph "cluster_{name:}" {{\nnode [color={color:}];\n'
              'color={color:};\nlabel="{name:}";\n'.format(
                  name=name, color=pick_color(name)))
    footer = "\n}"
    joined = []
    for location, children in calls:
        if location not in funcs:
            continue
        for child in sum(children, []):
            if child not in funcs:
                continue
            if (location, child) in drawn:
                continue
            joined.append('"{}" -> "{}";'.format(location, child))
            drawn.add((location, child))
    nodes = "\n".join(joined)
    return header+nodes+footer


def pick_color(goal):
    """Asign colors by module goal"""
    if goal[-3:] == ".py":
        goal = file_to_module(goal)
    for name, clr in zip(NAMES, COLORS):
        if goal.startswith(name):
            return clr
    return "green"

NAMES = ["instrument.larmor", "instrument.zoom", "instrument.loq", "technique.sans", "general.scans"]
COLORS = ["blue", "red", "cyan", "orange", "black"]


def make_dot(data):
    """Make a graph of the function calls"""
    data = list(data)
    funcs = set()
    seen = set()
    for x,y in data:
        for a, b in y:
            if a in funcs and a in seen:
                pass
                # funcs.remove(a)
            else:
                if a not in seen:
                    funcs.add(a)
                seen.add(a)
    drawn = set()
    clusters = "\n".join([make_cluster(x, y, funcs, drawn) for x, y in data])
    return 'digraph G {{\n rankdir="LR";\n {}\n}}'.format(clusters)


# dirs = ["general", "technique", "instrument"]
# dirs = ["technique",  "instrument"]

dirs = sys.argv[1:]

FILES = [
    os.path.join(directory, name)
    for d in dirs
    for (directory, _, names)
    in os.walk(os.path.relpath(os.path.join("..", d), ".."))
    for name in names
    if name[-3:] == ".py"]

with open("_".join(dirs) + ".dot", "w") as outfile:
    outfile.write(make_dot(map(load_file, FILES)))
