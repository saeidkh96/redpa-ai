from __future__ import annotations
import argparse
from datetime import datetime, timezone
from pathlib import Path
import subprocess


def main() -> int:
    parser = argparse.ArgumentParser(description='Create a PostgreSQL custom-format backup from redpa-postgres.')
    parser.add_argument('--output-dir', default='backups')
    parser.add_argument('--container', default='redpa-postgres')
    args = parser.parse_args()
    out_dir = Path(args.output_dir); out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    remote = f'/tmp/redpa-{stamp}.dump'; local = out_dir / f'redpa-{stamp}.dump'
    subprocess.run(['docker','exec',args.container,'pg_dump','-U','postgres','-d','redpa_ai','-Fc','-f',remote], check=True)
    subprocess.run(['docker','cp',f'{args.container}:{remote}',str(local)], check=True)
    subprocess.run(['docker','exec',args.container,'rm','-f',remote], check=True)
    print(local)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
