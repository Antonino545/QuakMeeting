"""
Event Capabilities Value Object for FlightDeck.
Exposes boolean capability flags to simplify presentation logic and prevent platform UI divergence.
"""
from dataclasses import dataclass
from typing import Optional, Any


@dataclass(frozen=True)
class EventCapabilities:
    """Explicit capabilities supported by a calendar event."""
    can_join: bool = False
    can_navigate: bool = False
    has_location: bool = False
    needs_travel: bool = False
    can_snooze: bool = True
    requires_acknowledgement: bool = False
    show_arrival_badge: bool = False
    show_in_call_badge: bool = False

    def to_dict(self) -> dict:
        return {
            "can_join": self.can_join,
            "can_navigate": self.can_navigate,
            "has_location": self.has_location,
            "needs_travel": self.needs_travel,
            "can_snooze": self.can_snooze,
            "requires_acknowledgement": self.requires_acknowledgement,
            "show_arrival_badge": self.show_arrival_badge,
            "show_in_call_badge": self.show_in_call_badge,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "EventCapabilities":
        return cls(
            can_join=bool(d.get("can_join", False)),
            can_navigate=bool(d.get("can_navigate", False)),
            has_location=bool(d.get("has_location", False)),
            needs_travel=bool(d.get("needs_travel", False)),
            can_snooze=bool(d.get("can_snooze", True)),
            requires_acknowledgement=bool(d.get("requires_acknowledgement", False)),
            show_arrival_badge=bool(d.get("show_arrival_badge", False)),
            show_in_call_badge=bool(d.get("show_in_call_badge", False)),
        )
