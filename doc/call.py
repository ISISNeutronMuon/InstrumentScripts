#!/usr/bin/env python

import ast
import os


def valid_module(m):
    return m.startswith("general") or m.startswith("technique") or m.startswith("instrument")


def handle_import(x):
    return [i.name for i in x.names if valid_module(i.name)]


def handle_import_from(x, f):
    # print(dir(x))
    if valid_module(x.module) or x.level > 0:
        if x.level == 0:
            header = ""
        elif x.level == 1:
            header = os.path.dirname(f).replace("/",".") + "."
        else:
            header = os.path.relname(os.path.dirname(f), "/".join([".." * (x.level-1)])) + "."
        return [header + x.module]
    return []


def handle(x, f):
    if isinstance(x, ast.Import):
        return handle_import(x)
    elif isinstance(x, ast.ImportFrom):
        return handle_import_from(x, f)
    else:
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
    base = data[0][:-3].replace("/",".")
    sources = data[1]
    lines = ['  "{}" -> "{}";'.format(base, source) for source in sources]
    return "\n".join(lines)


def make_dot(data):
    return "digraph G {{\n{}\n}}".format("\n\n".join([make_graphs(datum) for datum in data]))

dirs = ["general", "technique", "instrument"]

FILES = [
    os.path.join(directory, name)
    for d in dirs
    for (directory, _, names) in os.walk(os.path.relpath(os.path.join("..", d), ".."))
    for name in names
    if name[-3:] == ".py"]

print(make_dot(map(load_file, FILES)))
