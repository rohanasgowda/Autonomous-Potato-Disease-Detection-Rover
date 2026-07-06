from __future__ import annotations

from abc import ABC, abstractmethod


class GridMovementController(ABC):
    """Abstract interface for Phase 6 rover grid movement control."""

    @abstractmethod
    def move_to_grid_position(self, row_index: int, plant_index: int) -> None:
        """Move the rover to the requested row and plant grid location."""

    @abstractmethod
    def stop(self) -> None:
        """Stop rover motion at the current grid position."""


class NoOpGridMovementController(GridMovementController):
    """A no-op grid movement controller for hardware-agnostic workflows."""

    def move_to_grid_position(self, row_index: int, plant_index: int) -> None:
        return None

    def stop(self) -> None:
        return None
