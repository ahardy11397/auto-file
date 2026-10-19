"""Shared test fixtures.

The deterministic understander is forced for the whole suite so tests never
attempt a real Hugging Face download or GPU model load.
"""

import os

import pytest


@pytest.fixture(autouse=True)
def _mock_understander(monkeypatch):
    monkeypatch.setenv("AUTO_FILE_UNDERSTANDER", "mock")
    yield
