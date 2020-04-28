import os
from itertools import zip_longest
import rv.api
from typing import Generator


def create_sunvox_file(instruments_folder: str, fname: str) -> None:
    project = rv.api.Project()
    for ms in zip_longest(modules(instruments_folder, 'melody'), modules(instruments_folder, 'percussion')):
        for m in ms:
            project.attach_module(m)
            if m:
                project.connect(m, project.output)
    with open(fname, "wb") as f:
        project.write_to(f)


def modules(instruments_folder: str, subfolder: str) -> Generator[rv.api.m.Module, None, None]:
    for entry in sorted(os.scandir(os.path.join(instruments_folder, subfolder)), key=lambda e: e.name):
        if entry.name.endswith('.sunsynth'):
            synth = rv.api.read_sunvox_file(entry.path)
            yield synth.module


if __name__ == '__main__':
    create_sunvox_file('./instruments', 'svseq.sunvox')
