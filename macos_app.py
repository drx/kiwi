"""
macOS app bundle script

Usage:
    python macos_app.py py2app

On some systems you also need to fix @rpaths for PySide dylibs:

    $ otool -L dist/kiwi.app/Contents/Resources/lib/python2.7/lib-dynload/PySide/QtCore.so
    $ install_name_tool -change @rpath/libpyside-python2.7.1.2.dylib @executable_path/../Frameworks/libpyside-python2.7.1.2.dylib dist/kiwi.app/Contents/Resources/lib/python2.7/lib-dynload/PySide/QtCore.so
    $ install_name_tool -change @rpath/libshiboken-python2.7.1.2.dylib @executable_path/../Frameworks/libshiboken-python2.7.1.2.dylib dist/kiwi.app/Contents/Resources/lib/python2.7/lib-dynload/PySide/QtCore.so
    $ install_name_tool -change @rpath/libshiboken-python2.7.1.2.dylib @executable_path/../Frameworks/libshiboken-python2.7.1.2.dylib dist/kiwi.app/Contents/Resources/lib/python2.7/lib-dynload/PySide/QtGui.so
    $ install_name_tool -change @rpath/libpyside-python2.7.1.2.dylib @executable_path/../Frameworks/libpyside-python2.7.1.2.dylib dist/kiwi.app/Contents/Resources/lib/python2.7/lib-dynload/PySide/QtGui.so

"""

from setuptools import setup

APP = ['kiwi.py']
DATA_FILES = ['megadrive.so', 'images/pad.png', 'images/pad2.png', 'images/pad_big.png']

OPTIONS = {
    'argv_emulation': True,
    'includes': ['PySide.QtCore', 'PySide.QtGui'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
