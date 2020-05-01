# svseq

`svseq` is a simple pattern based step sequencer build around the [Novation Launchpad MK1](https://resource.novationmusic.com/support/product-downloads?product=Launchpad+MK1) and the [Sunvox sound engine](https://www.warmplace.ru/soft/sunvox/). It supports the [Ableton Link protocol](https://www.ableton.com/de/link/) and will synchronize automatically with other Link enabled applications.

## Prerequisites

- [Pipenv](https://pipenv.pypa.io/)
- [CMake](https://cmake.org/)

## Build

    git clone --recurse-submodules git@gitlab.com:hwestphal/svseq.git
    pipenv install --dev
    cd audio
    pipenv run python setup.py build_ext --inplace
    cd ..

## Prepare sunvox file

Put your melody and percussion instruments as `.sunsynth` files at `./instruments` and run:

    pipenv run python sunvox.py

This will create a `.sunvox` file containing all instruments in correct order. The file is read by `svseq` during startup.

All instruments should be bundled as meta-modules exposing appropriate controls (no. 6 to 9). Percussion instruments will be played at note C2, C3 up to C9.

## Run

    pipenv run python main.py
