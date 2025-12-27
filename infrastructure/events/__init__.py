"""
事件模块

包含事件总线实现
"""

from .event_bus import (
    get_event_emitter,
    event_emitter,
    on_event,
    emit,
)

__all__ = [
    "get_event_emitter",
    "event_emitter",
    "on_event",
    "emit",
]
