"""Baseline review probe. Run against df94b16; uses disposable data only."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.utils.file_manager import FileManager

with TemporaryDirectory() as temp, patch('src.utils.console.Console.print_colored'):
    root = Path(temp)
    base = root / 'profile'
    (base / 'data').mkdir(parents=True)
    (base / 'data' / 'world.txt').write_text('original')
    archive = root / 'backup.zip'
    with zipfile.ZipFile(archive, 'w') as handle:
        handle.writestr('data/world.txt', 'saved')
    result = FileManager.extract_backup(archive, base, base / 'data')
    print('Restore result:', result)
    print('World preserved:', (base / 'data' / 'world.txt').exists())
