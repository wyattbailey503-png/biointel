"""Test fixtures and test harness for BioIntel."""

from __future__ import annotations

import tempfile
from pathlib import Path
try:
    import pytest
    @pytest.fixture
    def temp_db() -> Database:
        """Provides a fresh isolated in-memory or temporary SQLite database."""
        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            db = Database(f.name)
            yield db
except ImportError:
    pass
