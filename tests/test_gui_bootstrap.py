from __future__ import annotations

from car_damage.gui.bootstrap import prepare_qt_environment


def test_windows_bootstrap_disables_qt_dpi_reconfiguration() -> None:
    environment: dict[str, str] = {}
    prepare_qt_environment(environment, platform_name="win32")
    assert environment["QT_QPA_PLATFORM"] == "windows:dpiawareness=0"
    assert environment["QT_SCALE_FACTOR_ROUNDING_POLICY"] == "PassThrough"


def test_normal_start_replaces_accidental_offscreen_platform() -> None:
    environment = {"QT_QPA_PLATFORM": "offscreen"}
    prepare_qt_environment(environment, platform_name="win32", allow_offscreen=False)
    assert environment["QT_QPA_PLATFORM"] == "windows:dpiawareness=0"


def test_smoke_test_preserves_offscreen_platform() -> None:
    environment = {"QT_QPA_PLATFORM": "offscreen"}
    prepare_qt_environment(environment, platform_name="win32", allow_offscreen=True)
    assert environment["QT_QPA_PLATFORM"] == "offscreen"


def test_non_windows_does_not_force_windows_plugin() -> None:
    environment: dict[str, str] = {}
    prepare_qt_environment(environment, platform_name="linux")
    assert "QT_QPA_PLATFORM" not in environment
