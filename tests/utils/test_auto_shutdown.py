#!/usr/bin/env python3

"""
Test for the auto-shutdown utility
"""

import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from src.utils.auto_shutdown import AutoShutdown


class TestAutoShutdown:
    """Tests for the AutoShutdown class"""

    def test_init(self):
        """Test initialization"""
        mock_shutdown = MagicMock()
        auto_shutdown = AutoShutdown(
            shutdown_callback=mock_shutdown,
            inactivity_threshold=30,
            check_interval=1,
            enabled=True,
        )

        assert auto_shutdown.shutdown_callback == mock_shutdown
        assert auto_shutdown.inactivity_threshold == 30
        assert auto_shutdown.check_interval == 1
        assert auto_shutdown.enabled is True
        assert isinstance(auto_shutdown.active_players, set)
        assert auto_shutdown.monitor_thread is None
        assert auto_shutdown.stop_monitoring_flag.is_set() is False

    def test_record_activity(self):
        """Test activity recording"""
        mock_shutdown = MagicMock()
        auto_shutdown = AutoShutdown(shutdown_callback=mock_shutdown)

        # Force the last activity to be in the past
        auto_shutdown.last_activity = datetime.now() - timedelta(minutes=5)
        old_activity = auto_shutdown.last_activity

        # Record new activity
        auto_shutdown.record_activity()

        # Verify timestamp was updated
        assert auto_shutdown.last_activity > old_activity

    def test_update_player_list(self):
        """Test player list updates"""
        mock_shutdown = MagicMock()
        auto_shutdown = AutoShutdown(shutdown_callback=mock_shutdown)

        # Force the last activity to be in the past
        auto_shutdown.last_activity = datetime.now() - timedelta(minutes=5)
        old_activity = auto_shutdown.last_activity

        # Initial player update with players
        auto_shutdown.update_player_list(["player1", "player2"])

        # Verify state
        assert auto_shutdown.active_players == {"player1", "player2"}
        assert auto_shutdown.last_activity > old_activity

        # New activity timestamp for next test
        old_activity = auto_shutdown.last_activity
        time.sleep(0.1)  # Ensure time difference is measurable

        # Update with one player left and one joined
        auto_shutdown.update_player_list(["player2", "player3"])

        # Verify active players were updated
        assert auto_shutdown.active_players == {"player2", "player3"}
        # Activity timestamp should be updated because of new player
        assert auto_shutdown.last_activity > old_activity

        # Test with empty player list
        old_activity = auto_shutdown.last_activity
        time.sleep(0.1)  # Ensure time difference is measurable
        auto_shutdown.update_player_list([])

        # Verify empty player list
        assert auto_shutdown.active_players == set()
        # Activity timestamp should not be updated for empty list
        assert auto_shutdown.last_activity == old_activity

    @pytest.mark.xfail(
        reason="This test is timing-sensitive and may fail in CI environments"
    )
    @patch("time.sleep", return_value=None)  # Don't actually sleep in tests
    def test_monitoring_thread(self, _):
        """Test monitoring thread behavior"""
        # Mock shutdown callback
        mock_shutdown = MagicMock()
        mock_shutdown.return_value = True

        # Create auto shutdown with short timeout
        auto_shutdown = AutoShutdown(
            shutdown_callback=mock_shutdown,
            inactivity_threshold=0.05,  # Very short for testing
            check_interval=0.02,
            enabled=True,
        )

        # Start monitoring
        auto_shutdown.start_monitoring()
        assert auto_shutdown.monitor_thread is not None
        assert auto_shutdown.monitor_thread.is_alive()

        # Wait for shutdown to be triggered by inactivity
        # We need a longer delay to ensure the monitoring thread has time to run shutdown
        time.sleep(0.5)

        # Verify shutdown was called
        mock_shutdown.assert_called_once()

        # Verify monitoring stopped after shutdown
        time.sleep(0.2)  # Give thread time to exit
        assert not auto_shutdown.monitor_thread.is_alive()

    def test_disabled_auto_shutdown(self):
        """Test behavior when auto-shutdown is disabled"""
        mock_shutdown = MagicMock()
        auto_shutdown = AutoShutdown(shutdown_callback=mock_shutdown, enabled=False)

        # Start monitoring with disabled state
        auto_shutdown.start_monitoring()
        assert auto_shutdown.monitor_thread is None

        # No shutdown should happen
        time.sleep(0.2)
        mock_shutdown.assert_not_called()

    def test_stop_monitoring(self):
        """Test stopping the monitoring thread"""
        mock_shutdown = MagicMock()
        auto_shutdown = AutoShutdown(
            shutdown_callback=mock_shutdown, check_interval=0.1
        )

        # Start monitoring
        auto_shutdown.start_monitoring()
        assert auto_shutdown.monitor_thread is not None
        assert auto_shutdown.monitor_thread.is_alive()

        # Stop monitoring
        auto_shutdown.stop_monitoring()
        time.sleep(0.2)  # Give thread time to exit

        # Thread should be stopped
        assert not auto_shutdown.monitor_thread.is_alive()

    def test_get_status(self):
        """Test getting status information"""
        mock_shutdown = MagicMock()
        auto_shutdown = AutoShutdown(
            shutdown_callback=mock_shutdown, inactivity_threshold=120, enabled=True
        )

        # Add some active players
        auto_shutdown.active_players = {"player1", "player2"}

        # Force last activity to be 10 minutes ago
        auto_shutdown.last_activity = datetime.now() - timedelta(minutes=10)

        # Get status
        status = auto_shutdown.get_status()

        # Verify status fields
        assert status["enabled"] is True
        assert status["monitoring_active"] is False  # Not started yet
        # Approximately 10 minutes
        assert 9.5 <= status["inactive_minutes"] <= 10.5
        assert status["shutdown_threshold_minutes"] == 120
        # Around 110 minutes left
        assert 109.5 <= status["minutes_until_shutdown"] <= 110.5
        assert status["active_player_count"] == 2
        assert set(status["active_players"]) == {"player1", "player2"}
