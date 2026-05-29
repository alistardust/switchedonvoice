"""Test configuration and fixtures."""
import pytest


@pytest.fixture
def qtbot(qtbot):
    """Override qtbot to automatically show widgets for visibility testing."""
    original_addWidget = qtbot.addWidget
    
    def addWidget_with_show(widget, *args, **kwargs):
        result = original_addWidget(widget, *args, **kwargs)
        widget.show()
        return result
    
    qtbot.addWidget = addWidget_with_show
    return qtbot
