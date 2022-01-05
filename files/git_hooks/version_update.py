#!/usr/bin/python3

import sys

from importlib import import_module
from pathlib import Path

current_path = Path(__file__).parent.parent
module_path = current_path.parent

sys.path.insert(0, str(module_path.absolute()))

version_module = import_module('property_mapper.version')

version = version_module.version
build = version_module.build

build += 1

version_file = module_path.joinpath('property_mapper/version.py')

print(version, build, version_file)

with open(version_file, 'w') as wf:
    vtext = (
        f"version = '{version}'\n"
        f"build = {build}\n"
    )

    wf.write(vtext)
