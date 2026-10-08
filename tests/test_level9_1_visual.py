"""Level 9.1 visual alert / permission UI tests."""

import pytest


def test_notification_helpers_exist():
    """Verify notification module exports needed for Level 9.1"""
    import os
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "src", "lib", "notifications.ts"))
    assert os.path.exists(path), "notifications.ts missing"
    content = open(path).read()
    assert "export function soundEnabled" in content
    assert "export function playAlertTone" in content
    assert "export async function requestNotificationPermission" in content


def test_alert_controls_export():
    """AlertControls component should be importable"""
    # Component file exists per git status
    import os
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "src", "components", "AlertControls.tsx"))
    assert os.path.exists(path), "AlertControls.tsx missing"
    content = open(path).read()
    assert "TEST ALERT" in content
    assert "playAlertTone" in content


def test_layout_has_overlay():
    """Layout should contain emergency overlay markup"""
    import os
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "src", "components", "Layout.tsx"))
    assert os.path.exists(path)
    content = open(path).read()
    assert "sos-emergency-overlay" in content
    assert "sos-perm-banner" in content
    assert "triggerEmergencyOverlay" in content
    assert "useLiveAlerts" in content


def test_index_css_has_flash_animation():
    """index.css should contain sos-flash animation for Level 9.1"""
    import os
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "src", "index.css"))
    assert os.path.exists(path)
    content = open(path).read()
    assert "@keyframes sos-flash" in content
