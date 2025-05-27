# Kiwi&nbsp;&nbsp; [![Coveralls](https://img.shields.io/coveralls/drx/kiwi.svg)](https://coveralls.io/github/drx/kiwi)

Kiwi is a simple Sega Genesis emulator.

<table><tr><td align="center"><img src="/images/kiwi.gif?raw=true"><br>Kiwi in action</td></tr></table>

### Quick start

#### Binary 
* [macOS app](https://github.com/drx/kiwi/releases/download/v0.1-alpha/kiwi-v0.1-alpha-macos.zip)

#### Running from source 
1. `$ git clone git://github.com/drx/kiwi.git` or [download the latest version](https://github.com/drx/kiwi/zipball/master)
2. `$ brew install qt@4` (macOS)<br>`$ sudo apt-get install libqt4-dev` (Linux)
2. `$ pip install PySide`
2. `$ make`
3. `$ ./kiwi.py`

### Requirements

* clang/gcc, make, Python 2.7
* Qt 4, PySide

### Acknowledgements

* The [hqx library](http://code.google.com/p/hqx/) is by Maxim Stepin and Cameron Zemek
* The Musashi library is by Karl Stenerud

### Notes

* Kiwi was written in 2013, with some bugs fixed and tests added more recently.
* There is no sound support. The Z80 processor is handled by dummy code. Some games do not work at all because of this.
* Tested on Linux and macOS.
* The bundled macOS doesn't work on some machines, in which case you have to run from source.
