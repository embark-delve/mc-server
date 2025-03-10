#!/usr/bin/env python3

"""
File manager utility for handling file operations like backups
"""

import datetime
import glob
import os
import shutil
from pathlib import Path
from typing import List, Optional, Tuple

from src.utils.console import Console


class FileManager:
    """Utility class for managing files and directories"""

    @staticmethod
    def ensure_directories(dirs: List[Path]) -> None:
        """
        Ensure that all specified directories exist

        Args:
            dirs: List of directories to create if they don't exist
        """
        for directory in dirs:
            os.makedirs(directory, exist_ok=True)
            Console.print_info(f"Ensured directory exists: {directory}")

    @staticmethod
    def get_file_size(file_path: Path) -> str:
        """
        Get human-readable file size

        Args:
            file_path: Path to the file

        Returns:
            str: Human-readable file size (e.g., "1.5 MB")
        """
        size_bytes = os.path.getsize(file_path)

        # Convert bytes to human-readable format
        units = ["B", "KB", "MB", "GB", "TB"]
        size = float(size_bytes)
        unit_index = 0

        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        return f"{size:.1f} {units[unit_index]}"

    @staticmethod
    def create_backup(
        source_dir: Path, backup_dir: Path, backup_name: Optional[str] = None
    ) -> Tuple[Path, str]:
        """
        Create a backup of a directory

        Args:
            source_dir: Directory to backup
            backup_dir: Directory to store backups
            backup_name: Optional name for the backup file

        Returns:
            Tuple[Path, str]: Path to the backup file and its size

        Raises:
            FileNotFoundError: If the source directory doesn't exist
            IOError: If the backup fails
        """
        # Ensure source directory exists
        if not os.path.exists(source_dir):
            raise FileNotFoundError(f"Source directory not found: {source_dir}")

        # Ensure backup directory exists
        os.makedirs(backup_dir, exist_ok=True)

        # Generate backup filename if not provided
        if not backup_name:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"minecraft_backup_{timestamp}.zip"

        backup_path = backup_dir / backup_name

        # Create the backup
        Console.print_info(f"Creating backup: {backup_path}")
        shutil.make_archive(
            # Remove .zip as make_archive adds it
            str(backup_path.with_suffix("")),
            "zip",
            root_dir=source_dir.parent,
            base_dir=source_dir.name,
        )

        # Correct the path to include .zip extension
        backup_path = backup_path.with_suffix(".zip")

        # Get the size of the backup
        backup_size = FileManager.get_file_size(backup_path)

        return backup_path, backup_size

    @staticmethod
    def list_backups(backup_dir: Path) -> List[Path]:
        """
        List all backup files in the backup directory

        Args:
            backup_dir: Directory containing backups

        Returns:
            List[Path]: List of backup file paths, sorted by date (newest first)
        """
        # Find all zip files in the backup directory
        backup_pattern = os.path.join(str(backup_dir), "*.zip")
        backup_files = [Path(f) for f in glob.glob(backup_pattern)]

        # Sort by modification time (newest first)
        backup_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

        return backup_files

    @staticmethod
    def cleanup_old_backups(backup_dir: Path, keep_count: int) -> int:
        """
        Remove old backups, keeping the specified number of recent backups

        Args:
            backup_dir: Directory containing backups
            keep_count: Number of recent backups to keep

        Returns:
            int: Number of backups removed
        """
        backup_files = FileManager.list_backups(backup_dir)

        # If we have more backups than the keep count, remove the oldest ones
        removed_count = 0
        if len(backup_files) > keep_count:
            to_remove = backup_files[keep_count:]

            for backup_file in to_remove:
                Console.print_warning(f"Removing old backup: {backup_file.name}")
                os.remove(backup_file)
                removed_count += 1

        return removed_count

    @staticmethod
    def extract_backup(
        backup_path: Path, extract_dir: Path, target_dir: Optional[Path] = None
    ) -> bool:
        """
        Extract a backup file to a directory

        Args:
            backup_path: Path to the backup zip file
            extract_dir: Directory to extract the backup to
            target_dir: Optional final target directory (if different from extract_dir)

        Returns:
            bool: True if extraction was successful, False otherwise
        """
        try:
            # Ensure the extraction directory exists
            os.makedirs(extract_dir, exist_ok=True)

            # Extract the backup
            Console.print_info(f"Extracting backup: {backup_path}")
            shutil.unpack_archive(str(backup_path), str(extract_dir), "zip")

            # If target_dir is specified and different from extract_dir,
            # move the extracted contents there
            if target_dir and target_dir != extract_dir:
                # Get the directory that was created by the extraction
                extracted_dirs = [d for d in extract_dir.iterdir() if d.is_dir()]
                if extracted_dirs:
                    source = extracted_dirs[0]

                    # Remove the target directory if it exists
                    if os.path.exists(target_dir):
                        shutil.rmtree(target_dir)

                    # Move the extracted directory to the target location
                    shutil.move(str(source), str(target_dir))

            return True
        except Exception as e:
            Console.print_error(f"Error extracting backup: {e}")
            return False
