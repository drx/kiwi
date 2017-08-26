def test_controllers(qtbot):
    from kiwi import MainWindow
    window = MainWindow()
    qtbot.addWidget(window)

    window.display.show_controllers()

    assert 'Start' in window.display.controllers_window.text()
