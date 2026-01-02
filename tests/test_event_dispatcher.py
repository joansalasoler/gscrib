import pytest
from unittest.mock import Mock
from gscrib.host.protocol import EventDispatcher
from gscrib.host.protocol.events import HostEvent


# --------------------------------------------------------------------
# Fixtures and helper classes
# --------------------------------------------------------------------

class MockEvent(HostEvent):
    pass

class OtherEvent(HostEvent):
    pass

class SubMockEvent(MockEvent):
    pass

@pytest.fixture
def dispatcher():
    return EventDispatcher()


# --------------------------------------------------------------------
# Test cases
# --------------------------------------------------------------------

def test_subscribe_and_dispatch(dispatcher):
    handler = Mock()
    event = MockEvent()
    dispatcher.subscribe(MockEvent, handler)
    dispatcher.dispatch(event)
    handler.assert_called_once_with(event)

def test_dispatch_inheritance(dispatcher):
    handler = Mock()
    dispatcher.subscribe(MockEvent, handler)
    event = SubMockEvent()
    dispatcher.dispatch(event)
    handler.assert_called_once_with(event)

def test_dispatch_no_inheritance_reverse(dispatcher):
    handler = Mock()
    dispatcher.subscribe(SubMockEvent, handler)
    event = MockEvent()
    dispatcher.dispatch(event)
    handler.assert_not_called()

def test_unsubscribe(dispatcher):
    handler = Mock()
    event = MockEvent()
    dispatcher.subscribe(MockEvent, handler)
    dispatcher.unsubscribe(MockEvent, handler)
    dispatcher.dispatch(event)
    handler.assert_not_called()

def test_unsubscribe_idempotent(dispatcher):
    handler = Mock()
    dispatcher.unsubscribe(MockEvent, handler)
    dispatcher.subscribe(MockEvent, handler)
    dispatcher.unsubscribe(MockEvent, handler)
    dispatcher.unsubscribe(MockEvent, handler)

def test_multiple_handlers(dispatcher):
    hanler1 = Mock()
    hanler2 = Mock()
    event = MockEvent()
    dispatcher.subscribe(MockEvent, hanler1)
    dispatcher.subscribe(MockEvent, hanler2)
    dispatcher.dispatch(event)
    hanler1.assert_called_once_with(event)
    hanler2.assert_called_once_with(event)

def test_event_filtering(dispatcher):
    hanler1 = Mock()
    hanler2 = Mock()
    event = MockEvent()
    dispatcher.subscribe(MockEvent, hanler1)
    dispatcher.subscribe(OtherEvent, hanler2)
    dispatcher.dispatch(event)
    hanler1.assert_called_once_with(event)
    hanler2.assert_not_called()
