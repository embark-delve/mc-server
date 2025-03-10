#!/usr/bin/env python3

"""
Auto-shutdown utility for Minecraft servers
"""

import time
import logging
import threading
from typing import Callable, List, Optional, Set
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("auto_shutdown")


class AutoShutdown:
    """
    Monitors player activity and automatically shuts down the server when inactive

    This class tracks player activity on a Minecraft server and triggers a shutdown
    when no players have been active for a specified period of time. This is useful
    for saving resources on cloud-based servers.
    """

    def __init__(
        self,
        shutdown_callback: Callable[[], bool],
        inactivity_threshold: int = 120,  # Default 2 hours in minutes
        check_interval: int = 5,  # Check every 5 minutes
        enabled: bool = True
    ):
        """
        Initialize the auto-shutdown monitor

        Args:
            shutdown_callback: Function to call to shut down the server
            inactivity_threshold: Minutes of inactivity before shutdown
            check_interval: How often to check for inactivity (minutes)
            enabled: Whether auto-shutdown is enabled
        """
        self.shutdown_callback = shutdown_callback
        self.inactivity_threshold = inactivity_threshold
        self.check_interval = check_interval
        self.enabled = enabled

        # Active players tracking
        self.active_players: Set[str] = set()

        # Activity timestamp
        self.last_activity: datetime = datetime.now()

        # Monitoring thread
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_monitoring_flag = threading.Event()

    def start_monitoring(self) -> None:
        """Start the inactivity monitoring thread"""
        if not self.enabled:
            logger.info("Auto-shutdown is disabled, not starting monitor")
            return

        # Reset activity timestamp
        self.record_activity()

        # Stop existing thread if running
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.stop_monitoring()

        # Start new monitoring thread
        self.stop_monitoring_flag.clear()
        self.monitor_thread = threading.Thread(
            target=self._monitor_activity,
            daemon=True,
            name="auto-shutdown-monitor"
        )
        self.monitor_thread.start()
        logger.info(
            f"Auto-shutdown monitor started. Will shut down after "
            f"{self.inactivity_threshold} minutes of inactivity."
        )

    def stop_monitoring(self) -> None:
        """Stop the inactivity monitoring thread"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.stop_monitoring_flag.set()
            self.monitor_thread.join(timeout=5.0)
            logger.info("Auto-shutdown monitor stopped")

    def record_activity(self) -> None:
        """Record server activity (reset the inactivity timer)"""
        self.last_activity = datetime.now()
        logger.debug("Server activity recorded")

    def update_player_list(self, players: List[str]) -> None:
        """
        Update the list of active players

        Args:
            players: List of player usernames currently online
        """
        # Convert to set for faster operations
        new_players = set(players)

        # Record activity if there are players
        if new_players:
            self.record_activity()

        # Check for newly joined players
        joined_players = new_players - self.active_players
        if joined_players:
            logger.info(f"Players joined: {', '.join(joined_players)}")
            self.record_activity()

        # Check for players who left
        left_players = self.active_players - new_players
        if left_players:
            logger.info(f"Players left: {', '.join(left_players)}")

        # Update the active player set
        self.active_players = new_players

    def _monitor_activity(self) -> None:
        """
        Monitor server activity and shut down if inactive

        This method runs in a separate thread and periodically checks if the server
        has been inactive for longer than the threshold. If so, it initiates a shutdown.
        """
        while not self.stop_monitoring_flag.is_set():
            try:
                # Check if server has been inactive for too long
                inactive_time = datetime.now() - self.last_activity
                inactive_minutes = inactive_time.total_seconds() / 60

                # Log remaining time at regular intervals
                if inactive_minutes % 15 < self.check_interval:
                    remaining_minutes = max(
                        0, self.inactivity_threshold - inactive_minutes)
                    logger.info(
                        f"Server inactive for {inactive_minutes:.1f} minutes. "
                        f"Will shut down in {remaining_minutes:.1f} minutes if no activity."
                    )

                # Check if we should shut down
                if inactive_minutes >= self.inactivity_threshold:
                    logger.info(
                        f"Server inactive for {inactive_minutes:.1f} minutes, "
                        f"exceeding threshold of {self.inactivity_threshold} minutes. "
                        f"Initiating shutdown."
                    )

                    # Call the shutdown callback
                    try:
                        self.shutdown_callback()
                        logger.info("Server shutdown successful")
                    except Exception as e:
                        logger.error(f"Error shutting down server: {e}")

                    # Stop monitoring after shutdown
                    self.stop_monitoring_flag.set()
                    break

            except Exception as e:
                logger.error(f"Error in auto-shutdown monitor: {e}")

            # Sleep for the check interval
            # Use small sleep intervals to respond to stop flag quickly
            for _ in range(int(self.check_interval * 60 / 5)):
                if self.stop_monitoring_flag.is_set():
                    break
                time.sleep(5)

    def get_status(self) -> dict:
        """
        Get the current status of the auto-shutdown monitor

        Returns:
            dict: Status information
        """
        inactive_time = datetime.now() - self.last_activity
        inactive_minutes = inactive_time.total_seconds() / 60
        remaining_minutes = max(
            0, self.inactivity_threshold - inactive_minutes)

        return {
            "enabled": self.enabled,
            "monitoring_active": bool(self.monitor_thread and self.monitor_thread.is_alive()),
            "inactive_minutes": round(inactive_minutes, 1),
            "shutdown_threshold_minutes": self.inactivity_threshold,
            "minutes_until_shutdown": round(remaining_minutes, 1),
            "last_activity": self.last_activity.isoformat(),
            "active_player_count": len(self.active_players),
            "active_players": list(self.active_players)
        }
