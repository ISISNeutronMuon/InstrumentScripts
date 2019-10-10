#!/usr/bin/env python

import ast
import os
import sys

from functools import singledispatch


def valid_module(m):
    return m.startswith("general") or m.startswith("technique") or m.startswith("instrument")


def file_to_module(f):
    return f[:-3].replace("/", ".")


def dir_to_module(f):
    return f.replace("/", ".")


@singledispatch
def names(x, f):
    return []

@names.register(ast.FunctionDef)
def _(x, f):
    subvalues = [calls(node, f) for node in ast.walk(x)]
    return [(x.name, subvalues)]

def load_file(f):
    with open(f, "r") as infile:
        data = infile.read()

    temp = ast.parse(data, f)

    result = [
        sum([names(node, f) for node in ast.walk(part)], [])
        for part in temp.body]
    return (f, sum(result, []))

@singledispatch
def calls(x, f):
    return []

@calls.register(ast.Call)
def calls(x, f):
    if type(x) != ast.Call:
        return []
    if isinstance(x.func, ast.Name):
        return [x.func.id]
    if isinstance(x.func, ast.Attribute):
        return [x.func.attr]
    return [str(x.func)]


def make_graphs(data):
    base = file_to_module(data[0])
    sources = data[1]
    lines = ['  "{}" -> "{}";'.format(base, source) for source in sources]
    return "\n".join(lines)


def make_node(module):
    style = " []"
    return '  "{}"{};'.format(module, style)


def make_cluster(name, calls, funcs, drawn):
    header = 'subgraph "cluster_{name:}" {{\nnode [color={color:}];\ncolor={color:};\nlabel="{name:}";\n'.format(
        name=name, color=pick_color(name))
    footer = "\n}"
    joined = []
    for a,b in calls:
        if a not in funcs:
            continue
        for c in sum(b, []):
            if c not in funcs:
                continue
            if (a, c) in drawn:
                continue
            joined.append('"{}" -> "{}";'.format(a, c))
            drawn.add((a,c))
    nodes = "\n".join(joined)
    return header+nodes+footer


def pick_color(name):
    if name[-3:] == ".py":
        name = file_to_module(name)
    for n, c in zip(NAMES, COLORS):
        if name.startswith(n):
            return c
    return "green"

NAMES = ["instrument.larmor", "instrument.zoom", "instrument.loq", "technique.sans", "general.scans"]
COLORS = ["blue", "red", "cyan", "orange", "black"]


def make_dot(data):
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
