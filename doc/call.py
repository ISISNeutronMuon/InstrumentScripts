#!/usr/bin/env python

import ast
import os

from functools import singledispatch


def valid_module(m):
    return m.startswith("general") or m.startswith("technique") or m.startswith("instrument")


def file_to_module(f):
    return f[:-3].replace("/", ".")


def dir_to_module(f):
    return f.replace("/", ".")


@singledispatch
def handle(x, f):
    return []


@handle.register(ast.Import)
def _(x, f):
    return [i.name for i in x.names if valid_module(i.name)]


@handle.register(ast.ImportFrom)
def _(x, f):
    # print(dir(x))
    if valid_module(x.module) or x.level > 0:
        if x.level == 0:
            header = ""
        elif x.level == 1:
            header = dir_to_module(os.path.dirname(f)) + "."
        else:
            header = os.path.relname(
                os.path.dirname(f), "/".join([".." * (x.level-1)])) + "."
        return [header + x.module]
    return []


def load_file(f):
    with open(f, "r") as infile:
        data = infile.read()

    temp = ast.parse(data, f)

    result = [
        sum([handle(node, f) for node in ast.walk(part)], [])
        for part in temp.body]
    return (f, sum(result, []))


def make_graphs(data):
    base = file_to_module(data[0])
    sources = data[1]
    lines = ['  "{}" -> "{}";'.format(base, source) for source in sources]
    return "\n".join(lines)


def make_node(module):
    style = " []"
    return '  "{}"{};'.format(module, style)


def make_cluster(name, color, modules):
    header = 'subgraph "cluster_{name:}" {{\nnode [color={color:}];\ncolor={color:};\nlabel="{name:}";\n'.format(
        name=name, color=color)
    nodes = "\n".join([make_node(m) for m in modules if m.startswith(name)])
    footer = "\n}"
    return header+nodes+footer


NAMES = ["instrument.larmor", "instrument.zoom", "instrument.loq", "technique.sans", "general.scans"]
COLORS = ["blue", "red", "cyan", "black", "black"]


def make_dot(data):
    data = list(data)
    modules = sum([d[1] for d in data], []) + [file_to_module(d[0]) for d in data if d[1]]
    modules = [m for m in modules if "test" not in m]
    clusters = [make_cluster(name, color, modules) for (name, color) in zip(NAMES, COLORS)]
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
