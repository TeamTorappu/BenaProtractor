#----------------------------------------
# 打包器
#----------------------------------------
import datetime
import json
import os
from pathlib import Path
import sys
import tempfile
import zipfile

from app_settings import normalize_settings


SOURCE_DIR = Path(__file__).resolve().parent
RESOURCES = (
    'icon/icon.ico',
    'translation/bena_dictionary.json',
    'translation/anne_dictionary.json',
    'table_dummies/global_buff_dummy.json',
)


def create_archive(source_dir=None, output_dir=None, date=None):
    source_dir = Path(source_dir or SOURCE_DIR).resolve()
    output_dir = Path(output_dir or source_dir / 'output').resolve()
    date = date or datetime.date.today()
    executable = source_dir / 'dist' / 'main.exe'
    files = [(executable, '贝娜的量角器.exe')]
    files.extend((source_dir / name, name) for name in RESOURCES)
    missing = [str(path) for path, _ in files if not path.is_file()]
    if missing:
        raise FileNotFoundError('Missing package files: ' + ', '.join(missing))
    if not executable.stat().st_size:
        raise ValueError('The built executable is empty.')

    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / f'贝娜的量角器 {date.year}.{date.month}.{date.day}.zip'
    descriptor, temporary = tempfile.mkstemp(prefix='.package-', suffix='.tmp', dir=output_dir)
    os.close(descriptor)
    temporary = Path(temporary)
    try:
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED) as package:
            for path, name in files:
                package.write(path, arcname=name)
            # Release defaults come from the application, never the builder's preferences.
            package.writestr('.settings.json', json.dumps(
                normalize_settings({}), ensure_ascii=False, indent=2) + '\n')
        with zipfile.ZipFile(temporary) as package:
            invalid = package.testzip()
            if invalid:
                raise ValueError('Invalid archive entry: ' + invalid)
        os.replace(temporary, archive)
    finally:
        temporary.unlink(missing_ok=True)
    return archive


def main():
    try:
        archive = create_archive()
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print(f'Packaging failed: {error}', file=sys.stderr)
        return 1
    print(f'Package created: {archive}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
