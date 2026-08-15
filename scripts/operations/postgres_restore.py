from __future__ import annotations
import argparse
from pathlib import Path
import subprocess


def main() -> int:
    parser=argparse.ArgumentParser(description='Restore a RedPA PostgreSQL backup. Destructive; requires explicit confirmation.')
    parser.add_argument('backup')
    parser.add_argument('--container', default='redpa-postgres')
    parser.add_argument('--confirm', action='store_true')
    args=parser.parse_args()
    if not args.confirm:
        raise SystemExit('Refusing restore without --confirm.')
    backup=Path(args.backup)
    if not backup.is_file(): raise SystemExit(f'Backup not found: {backup}')
    remote='/tmp/redpa-restore.dump'
    subprocess.run(['docker','cp',str(backup),f'{args.container}:{remote}'], check=True)
    subprocess.run(['docker','exec',args.container,'pg_restore','-U','postgres','-d','redpa_ai','--clean','--if-exists','--no-owner',remote], check=True)
    subprocess.run(['docker','exec',args.container,'rm','-f',remote], check=True)
    print('Restore completed.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
