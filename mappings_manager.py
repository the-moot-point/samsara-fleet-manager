"""Helpers for loading Samsara mapping CSVs."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Optional, Tuple


class MappingsManager:
    """Load and query mapping files used by the driver manager."""

    def __init__(self, mappings_dir: str = "./mappings"):
        self.mappings_dir = Path(mappings_dir)
        self.positions: Dict[str, str] = {}
        self.locations: Dict[str, Tuple[str, str]] = {}
        self.never_positions: set[str] = set()
        self._load_mappings()

    # ------------------------------------------------------------------
    def _load_mappings(self) -> None:
        self._load_positions()
        self._load_locations()
        self._load_never_positions()

    def _load_positions(self) -> None:
        path = self.mappings_dir / "positions.csv"
        if not path.exists():
            return
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                position = row.get("position", "").strip()
                tag_id = row.get("id", "").strip()
                if position:
                    self.positions[position] = tag_id

    def _load_locations(self) -> None:
        path = self.mappings_dir / "locations.csv"
        if not path.exists():
            return
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                location = row.get("location", "").strip()
                tag_id = row.get("id", "").strip()
                tz = row.get("timezone", "").strip()
                if location:
                    self.locations[location] = (tag_id, tz)

    def _load_never_positions(self) -> None:
        path = self.mappings_dir / "never_positions.csv"
        if not path.exists():
            return
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pos = row.get("never_position", "").strip()
                if pos:
                    self.never_positions.add(pos)

    # ------------------------------------------------------------------
    def get_position_tag(self, position: str) -> Optional[str]:
        """Return the Samsara tag ID for a position."""
        return self.positions.get(position)

    def get_location_info(self, location: str) -> Tuple[Optional[str], Optional[str]]:
        """Return (tag_id, timezone) for a location."""
        return self.locations.get(location, (None, None))

    def is_position_allowed(self, position: str) -> bool:
        """Return True if the position is not in the exclusion list."""
        return position not in self.never_positions

    def validate_new_hire(self, record: Dict[str, str]) -> Tuple[bool, str]:
        """Validate a new hire record using the mapping rules."""
        position = record.get("Position", "").strip()
        location = record.get("Location_Desc", "").strip()
        status = record.get("Employee_Status", "").strip().lower()

        if status != "active":
            return False, "Inactive employee"
        if not self.is_position_allowed(position):
            return False, "Position excluded"
        if position not in self.positions:
            return False, "Unknown position"
        if location not in self.locations:
            return False, "Unknown location"
        return True, ""
