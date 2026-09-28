"""Regression tests for the Samsung deeplink matcher.

Place this file at tests/test_matcher.py in the project repository.
Expected project layout:
    app/deeplink/matcher.py
    data/deeplinks.json
    tests/test_matcher.py

Run from the repository root with: python -m pytest -q
"""

from pathlib import Path

import pytest

from app.deeplink.matcher import DeeplinkMatcher

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEEPLINK_FILE = PROJECT_ROOT / "data" / "deeplinks.json"


@pytest.fixture(scope="module")
def matcher():
    if not DEEPLINK_FILE.exists():
        pytest.fail(
            f"Could not find deeplink catalogue at {DEEPLINK_FILE}. "
            "Update DEEPLINK_FILE if your project stores it elsewhere."
        )
    return DeeplinkMatcher(str(DEEPLINK_FILE))


def match(matcher, action_name, steps, capsys, description=""):
    result = matcher.build_step_group_result(
        action_name=action_name,
        description=description,
        steps=steps,
    )
    # The matcher currently prints its top candidates; keep test output readable.
    capsys.readouterr()
    return result


def test_enable_bluetooth_scanning_matches_scanning_toggle(matcher, capsys):
    result = match(
        matcher,
        "Enable Bluetooth scanning",
        ["Enable Bluetooth scanning"],
        capsys,
    )
    actionable = result["actionableDeeplink"]
    assert actionable is not None
    assert actionable["originalType"] == "onURL"
    assert result["validationDeeplink"]["key"] == "Bluetooth scanning"
    assert "scanning" in actionable["description"].lower()


def test_disable_bluetooth_scanning_matches_scanning_toggle(matcher, capsys):
    result = match(
        matcher,
        "Disable Bluetooth scanning",
        ["Disable Bluetooth scanning"],
        capsys,
    )
    actionable = result["actionableDeeplink"]
    assert actionable is not None
    assert actionable["originalType"] == "offURL"
    assert result["validationDeeplink"]["key"] == "Bluetooth scanning"
    assert "scanning" in actionable["description"].lower()


def test_open_bluetooth_scanning_matches_navigation_entry(matcher, capsys):
    result = match(
        matcher,
        "Open Bluetooth scanning settings",
        ["Open Bluetooth scanning settings"],
        capsys,
    )
    actionable = result["actionableDeeplink"]
    assert actionable is not None
    assert actionable["originalType"] == "onClickURL"
    assert actionable["message"] == "View Bluetooth scanning"
    assert result["validationDeeplink"]["key"] == "Bluetooth scanning"


def test_enable_bluetooth_does_not_select_scanning_entry(matcher, capsys):
    result = match(
        matcher,
        "Enable Bluetooth",
        ["Enable Bluetooth"],
        capsys,
    )
    actionable = result["actionableDeeplink"]
    assert actionable is not None
    assert actionable["originalType"] == "onURL"
    assert result["validationDeeplink"]["key"] == "Bluetooth"
    assert "scanning" not in actionable["description"].lower()


def test_touch_and_hold_delay_returns_its_settings_entry(matcher, capsys):
    result = match(
        matcher,
        "Change Touch and Hold Delay",
        ["Set the Touch and Hold Delay to long"],
        capsys,
    )
    actionable = result["actionableDeeplink"]
    assert actionable is not None
    assert actionable["message"] == "View Touch and hold delay"
    assert result["validationDeeplink"]["key"] == "Touch and hold delay"


def test_unrelated_email_problem_does_not_get_random_deeplink(matcher, capsys):
    result = match(
        matcher,
        "My email is not working",
        ["My email is not working"],
        capsys,
    )
    assert result["actionableDeeplink"] is None
    assert result["validationDeeplink"] is None
