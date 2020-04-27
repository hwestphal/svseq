# svseq

`svseq` is a simple pattern based step sequencer build around a [Novation Launchpad MK1](https://resource.novationmusic.com/support/product-downloads?product=Launchpad+MK1) and the [Sunvox sound engine](https://www.warmplace.ru/soft/sunvox/). It supports the [Ableton Link protocol](https://www.ableton.com/de/link/) and will synchronize automatically with other Link enabled applications.

## Prerequisites

- [Pipenv](https://pipenv.pypa.io/)
- [CMake](https://cmake.org/)

## Build

    git clone --recurse-submodules git@gitlab.com:hwestphal/svseq.git
    pipenv install --dev
    cd audio
    pipenv run python setup.py build_ext --inplace
    cd ..

## Run

    pipenv run python main.py
