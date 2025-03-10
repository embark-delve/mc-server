#!/usr/bin/env python3

"""
Monitoring utilities for Minecraft servers
Collects metrics and exports them to Prometheus or CloudWatch
"""

import os
import time
import json
import threading
import logging
import platform
import subprocess
from typing import Dict, List, Optional, Union, Any, Callable
from pathlib import Path

# Import optional dependencies - these will be available only if installed
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

try:
    import prometheus_client as prom
    from prometheus_client import start_http_server
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("monitoring")


class ServerMonitor:
    """
    Monitors a Minecraft server and provides metrics
    """

    def __init__(
        self,
        server_type: str,
        metrics_port: int = 9100,
        metrics_path: str = "/metrics",
        collect_interval: int = 15,  # seconds
        enable_prometheus: bool = True,
        enable_cloudwatch: bool = False,
        cloudwatch_namespace: str = "Minecraft",
        server_name: str = "minecraft-server",
        server_id: Optional[str] = None,
        metrics_dir: Optional[Path] = None
    ):
        """
        Initialize the server monitor

        Args:
            server_type: Type of server (docker, aws, kubernetes)
            metrics_port: Port for Prometheus metrics server
            metrics_path: Path for Prometheus metrics
            collect_interval: Interval between metrics collections in seconds
            enable_prometheus: Whether to enable Prometheus metrics
            enable_cloudwatch: Whether to enable CloudWatch metrics
            cloudwatch_namespace: CloudWatch namespace for metrics
            server_name: Name of this server (for labeling metrics)
            server_id: Optional server ID (e.g., EC2 instance ID for AWS)
            metrics_dir: Directory to store metrics files
        """
        self.server_type = server_type
        self.metrics_port = metrics_port
        self.metrics_path = metrics_path
        self.collect_interval = collect_interval
        self.server_name = server_name
        self.server_id = server_id or self._get_server_id()
        self.metrics_dir = metrics_dir or Path.cwd() / "metrics"

        # Metrics configuration
        self.enable_prometheus = enable_prometheus and PROMETHEUS_AVAILABLE
        self.enable_cloudwatch = enable_cloudwatch and BOTO3_AVAILABLE
        self.cloudwatch_namespace = cloudwatch_namespace

        # Metrics collectors
        self.metrics = self._initialize_metrics()

        # Ensure metrics directory exists
        os.makedirs(self.metrics_dir, exist_ok=True)

        # Threads
        self._collector_thread: Optional[threading.Thread] = None
        self._running = False

        # Initialize backends
        if self.enable_prometheus:
            self._initialize_prometheus()

        if self.enable_cloudwatch:
            self._initialize_cloudwatch()

    def start(self) -> None:
        """Start collecting metrics"""
        if self._collector_thread and self._collector_thread.is_alive():
            logger.warning("Metrics collector is already running")
            return

        self._running = True
        self._collector_thread = threading.Thread(
            target=self._collect_metrics_loop)
        self._collector_thread.daemon = True
        self._collector_thread.start()
        logger.info(
            f"Started metrics collection every {self.collect_interval} seconds")

    def stop(self) -> None:
        """Stop collecting metrics"""
        self._running = False
        if self._collector_thread:
            self._collector_thread.join(timeout=1.0)
        logger.info("Stopped metrics collection")

    def collect_metrics(self) -> Dict[str, float]:
        """
        Collect metrics from the server

        Returns:
            Dict[str, float]: Dictionary of metric names and values
        """
        metrics = {}

        # System metrics
        if PSUTIL_AVAILABLE:
            # CPU usage
            metrics["system_cpu_percent"] = psutil.cpu_percent(interval=0.1)

            # Memory usage
            memory = psutil.virtual_memory()
            metrics["system_memory_total"] = memory.total
            metrics["system_memory_available"] = memory.available
            metrics["system_memory_used"] = memory.used
            metrics["system_memory_percent"] = memory.percent

            # Disk usage
            disk = psutil.disk_usage(str(self.metrics_dir))
            metrics["system_disk_total"] = disk.total
            metrics["system_disk_used"] = disk.used
            metrics["system_disk_free"] = disk.free
            metrics["system_disk_percent"] = disk.percent

            # Network IO
            net_io = psutil.net_io_counters()
            metrics["system_net_bytes_sent"] = net_io.bytes_sent
            metrics["system_net_bytes_recv"] = net_io.bytes_recv

        # Server-specific metrics based on type
        if self.server_type == "docker":
            docker_metrics = self._collect_docker_metrics()
            metrics.update(docker_metrics)
        elif self.server_type == "aws":
            aws_metrics = self._collect_aws_metrics()
            metrics.update(aws_metrics)

        # Log metrics to file
        self._log_metrics_to_file(metrics)

        # Update Prometheus metrics if enabled
        if self.enable_prometheus:
            self._update_prometheus_metrics(metrics)

        # Send to CloudWatch if enabled
        if self.enable_cloudwatch:
            self._send_to_cloudwatch(metrics)

        return metrics

    def get_metrics(self) -> Dict[str, float]:
        """
        Get the last collected metrics

        Returns:
            Dict[str, float]: Dictionary of metric names and values
        """
        try:
            metrics_file = self.metrics_dir / "latest_metrics.json"
            if not os.path.exists(metrics_file):
                return {}

            with open(metrics_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to read metrics file: {e}")
            return {}

    def _initialize_metrics(self) -> Dict[str, Any]:
        """
        Initialize metrics collectors

        Returns:
            Dict of metric objects
        """
        metrics = {}

        if self.enable_prometheus:
            # Core metrics
            metrics["player_count"] = prom.Gauge(
                "minecraft_player_count",
                "Number of connected players",
                ["server_name", "server_id"]
            )

            metrics["heap_used"] = prom.Gauge(
                "minecraft_heap_used_bytes",
                "Java heap used in bytes",
                ["server_name", "server_id"]
            )

            metrics["heap_max"] = prom.Gauge(
                "minecraft_heap_max_bytes",
                "Java heap maximum in bytes",
                ["server_name", "server_id"]
            )

            metrics["cpu_usage"] = prom.Gauge(
                "minecraft_cpu_usage_percent",
                "CPU usage percentage",
                ["server_name", "server_id"]
            )

            metrics["memory_usage"] = prom.Gauge(
                "minecraft_memory_usage_percent",
                "Memory usage percentage",
                ["server_name", "server_id"]
            )

            metrics["uptime"] = prom.Gauge(
                "minecraft_uptime_seconds",
                "Server uptime in seconds",
                ["server_name", "server_id"]
            )

            metrics["tps"] = prom.Gauge(
                "minecraft_tps",
                "Ticks per second",
                ["server_name", "server_id"]
            )

        return metrics

    def _initialize_prometheus(self) -> None:
        """Initialize Prometheus metrics server"""
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus client library not available")
            return

        try:
            logger.info(
                f"Starting Prometheus metrics server on port {self.metrics_port}")
            start_http_server(self.metrics_port)
        except Exception as e:
            logger.error(f"Failed to start Prometheus metrics server: {e}")

    def _initialize_cloudwatch(self) -> None:
        """Initialize CloudWatch client"""
        if not BOTO3_AVAILABLE:
            logger.warning(
                "boto3 library not available for CloudWatch metrics")
            return

        try:
            self.cloudwatch = boto3.client('cloudwatch')
            logger.info(
                f"Initialized CloudWatch metrics client with namespace {self.cloudwatch_namespace}")
        except Exception as e:
            logger.error(f"Failed to initialize CloudWatch client: {e}")
            self.enable_cloudwatch = False

    def _collect_metrics_loop(self) -> None:
        """Metrics collection loop"""
        while self._running:
            try:
                self.collect_metrics()
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")

            time.sleep(self.collect_interval)

    def _log_metrics_to_file(self, metrics: Dict[str, float]) -> None:
        """
        Log metrics to a file

        Args:
            metrics: Dictionary of metrics to log
        """
        try:
            # Save to latest metrics file
            latest_file = self.metrics_dir / "latest_metrics.json"
            with open(latest_file, 'w') as f:
                json.dump(metrics, f, indent=2)

            # Also save with timestamp for history
            timestamp = int(time.time())
            history_file = self.metrics_dir / f"metrics_{timestamp}.json"
            with open(history_file, 'w') as f:
                json.dump(metrics, f, indent=2)

            # Cleanup old files (keep last 100)
            self._cleanup_old_metrics_files(100)
        except IOError as e:
            logger.warning(f"Failed to write metrics to file: {e}")

    def _cleanup_old_metrics_files(self, keep_count: int) -> None:
        """
        Clean up old metrics files

        Args:
            keep_count: Number of files to keep
        """
        try:
            metrics_files = list(self.metrics_dir.glob("metrics_*.json"))
            metrics_files.sort(key=lambda f: os.path.getmtime(f))

            if len(metrics_files) > keep_count:
                for old_file in metrics_files[:-keep_count]:
                    os.remove(old_file)
        except Exception as e:
            logger.warning(f"Failed to clean up old metrics files: {e}")

    def _update_prometheus_metrics(self, metrics: Dict[str, float]) -> None:
        """
        Update Prometheus metrics

        Args:
            metrics: Dictionary of metrics to update
        """
        if not self.enable_prometheus:
            return

        labels = {"server_name": self.server_name, "server_id": self.server_id}

        # Update Prometheus metrics from collected metrics
        for metric_name, metric_obj in self.metrics.items():
            if metric_name in metrics:
                metric_obj.labels(**labels).set(metrics[metric_name])

    def _send_to_cloudwatch(self, metrics: Dict[str, float]) -> None:
        """
        Send metrics to CloudWatch

        Args:
            metrics: Dictionary of metrics to send
        """
        if not self.enable_cloudwatch or not BOTO3_AVAILABLE:
            return

        try:
            metric_data = []

            for name, value in metrics.items():
                metric_data.append({
                    'MetricName': name,
                    'Dimensions': [
                        {'Name': 'ServerName', 'Value': self.server_name},
                        {'Name': 'ServerId', 'Value': self.server_id},
                        {'Name': 'ServerType', 'Value': self.server_type}
                    ],
                    'Value': value,
                    'Unit': self._get_metric_unit(name)
                })

            # Split into chunks of 20 (CloudWatch API limit)
            for i in range(0, len(metric_data), 20):
                chunk = metric_data[i:i+20]
                self.cloudwatch.put_metric_data(
                    Namespace=self.cloudwatch_namespace,
                    MetricData=chunk
                )

            logger.debug(f"Sent {len(metric_data)} metrics to CloudWatch")
        except Exception as e:
            logger.error(f"Failed to send metrics to CloudWatch: {e}")

    def _get_metric_unit(self, metric_name: str) -> str:
        """
        Get the appropriate CloudWatch unit for a metric

        Args:
            metric_name: Name of the metric

        Returns:
            str: CloudWatch unit
        """
        if "percent" in metric_name.lower():
            return "Percent"
        elif "bytes" in metric_name.lower() or "memory" in metric_name.lower():
            return "Bytes"
        elif "count" in metric_name.lower():
            return "Count"
        elif "seconds" in metric_name.lower() or "time" in metric_name.lower():
            return "Seconds"
        else:
            return "None"

    def _get_server_id(self) -> str:
        """
        Get a unique identifier for this server

        Returns:
            str: Server ID
        """
        # For Docker, use hostname
        if self.server_type == "docker":
            return platform.node()

        # For AWS, try to get instance ID
        if self.server_type == "aws" and BOTO3_AVAILABLE:
            try:
                # First try IMDSv2
                token_cmd = ["curl", "-s", "-X", "PUT", "http://169.254.169.254/latest/api/token",
                             "-H", "X-aws-ec2-metadata-token-ttl-seconds: 60"]
                token_proc = subprocess.run(
                    token_cmd, capture_output=True, text=True)
                token = token_proc.stdout.strip()

                # Get instance ID using token
                if token:
                    id_cmd = ["curl", "-s", "-H", f"X-aws-ec2-metadata-token: {token}",
                              "http://169.254.169.254/latest/meta-data/instance-id"]
                    id_proc = subprocess.run(
                        id_cmd, capture_output=True, text=True)
                    instance_id = id_proc.stdout.strip()
                    if instance_id:
                        return instance_id
            except Exception:
                pass

        # Fallback to hostname
        return platform.node()

    def _collect_docker_metrics(self) -> Dict[str, float]:
        """
        Collect Docker-specific metrics

        Returns:
            Dict[str, float]: Docker-specific metrics
        """
        metrics = {}

        try:
            # Get Docker stats
            cmd = ["docker", "stats", "minecraft-server", "--no-stream", "--format",
                   "{{.CPUPerc}}|{{.MemUsage}}|{{.MemPerc}}|{{.NetIO}}|{{.BlockIO}}"]
            proc = subprocess.run(cmd, capture_output=True, text=True)

            if proc.returncode == 0 and proc.stdout:
                parts = proc.stdout.strip().split('|')
                if len(parts) >= 5:
                    # CPU percentage (remove % sign)
                    cpu_perc = parts[0].strip().rstrip('%')
                    metrics["container_cpu_percent"] = float(cpu_perc)

                    # Memory usage
                    mem_parts = parts[1].split('/')
                    if len(mem_parts) == 2:
                        mem_used = self._parse_size(mem_parts[0].strip())
                        mem_limit = self._parse_size(mem_parts[1].strip())
                        metrics["container_memory_used"] = mem_used
                        metrics["container_memory_limit"] = mem_limit

                    # Memory percentage (remove % sign)
                    mem_perc = parts[2].strip().rstrip('%')
                    metrics["container_memory_percent"] = float(mem_perc)

                    # Network IO
                    net_parts = parts[3].split('/')
                    if len(net_parts) == 2:
                        net_in = self._parse_size(net_parts[0].strip())
                        net_out = self._parse_size(net_parts[1].strip())
                        metrics["container_network_in"] = net_in
                        metrics["container_network_out"] = net_out

                    # Block IO
                    block_parts = parts[4].split('/')
                    if len(block_parts) == 2:
                        block_in = self._parse_size(block_parts[0].strip())
                        block_out = self._parse_size(block_parts[1].strip())
                        metrics["container_block_in"] = block_in
                        metrics["container_block_out"] = block_out
        except Exception as e:
            logger.warning(f"Failed to collect Docker metrics: {e}")

        return metrics

    def _collect_aws_metrics(self) -> Dict[str, float]:
        """
        Collect AWS-specific metrics

        Returns:
            Dict[str, float]: AWS-specific metrics
        """
        metrics = {}

        if not BOTO3_AVAILABLE:
            return metrics

        try:
            # Get CloudWatch metrics for the instance
            pass  # This would be implemented with boto3 CloudWatch get_metric_data

        except Exception as e:
            logger.warning(f"Failed to collect AWS metrics: {e}")

        return metrics

    def _parse_size(self, size_str: str) -> float:
        """
        Parse a size string (e.g., "1.5GB") to bytes

        Args:
            size_str: Size string to parse

        Returns:
            float: Size in bytes
        """
        try:
            # Remove any non-numeric/non-decimal prefix
            value = ""
            for char in size_str:
                if char.isdigit() or char == '.':
                    value += char
                else:
                    break

            value = float(value)

            # Get unit
            unit = size_str[len(str(value)):].strip().upper()

            # Convert to bytes
            if unit.startswith('K'):
                return value * 1024
            elif unit.startswith('M'):
                return value * 1024 * 1024
            elif unit.startswith('G'):
                return value * 1024 * 1024 * 1024
            elif unit.startswith('T'):
                return value * 1024 * 1024 * 1024 * 1024
            else:
                return value
        except (ValueError, IndexError):
            return 0.0
