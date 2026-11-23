#!/usr/bin/env python3
"""WP Fleet Manager: auditoría local para instalaciones WordPress.

Solo inspecciona carpetas bajo --root. No modifica las instalaciones.
WP-CLI, cuando se permite, ejecuta consultas sin actualización de contenido.
Nunca ejecutar como root.
"""
import argparse
import csv
import html
import os
import shutil
import subprocess
from pathlib import Path

SKIP_DIRS = {'.git', '.cache', 'node_modules', 'vendor', 'tmp', 'temp', 'logs', 'backup', 'backups', '.trash', 'mail', 'etc', 'ssl', 'virtfs'}

def discover(root: Path, max_depth: int, max_sites: int):
    found = []
    root = root.resolve()
    for base, dirs, files in os.walk(root, followlinks=False):
        current = Path(base)
        depth = len(current.relative_to(root).parts)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not (current / d).is_symlink()]
        if 'wp-config.php' in files and (current / 'wp-includes').is_dir() and (current / 'wp-admin').is_dir():
            found.append(current)
            dirs[:] = []
            if len(found) >= max_sites:
                break
        elif depth >= max_depth:
            dirs[:] = []
    return found

def run_wpcli(path: Path, args, timeout):
    cmd = ['wp', *args, f'--path={path}', '--skip-plugins', '--skip-themes', '--no-color']
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False,
                           stdin=subprocess.DEVNULL)
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, '', f'Tiempo de espera excedido ({timeout}s)'
    except (OSError, UnicodeError) as exc:
        return 125, '', str(exc)

def audit(path, use_wpcli, timeout):
    row = {'ruta': str(path), 'estado': 'Detectado', 'version_wp': '', 'plugins_pendientes': '', 'temas_pendientes': '', 'detalle': ''}
    if not use_wpcli:
        row['detalle'] = 'WP-CLI no disponible o desactivado'
        return row
    rc, out, err = run_wpcli(path, ['core', 'version'], timeout)
    if rc != 0:
        row.update(estado='Revisar', detalle=('WP-CLI core version: ' + err)[:250])
        return row
    row['version_wp'] = out.splitlines()[0] if out else ''
    issues = []
    for kind, key in [('plugin', 'plugins_pendientes'), ('theme', 'temas_pendientes')]:
        rc, out, err = run_wpcli(path, [kind, 'list', '--update=available', '--field=name'], timeout)
        if rc != 0:
            issues.append(kind + ': ' + err[:100])
        else:
            row[key] = len([x for x in out.splitlines() if x.strip()])
    if issues:
        row['estado'] = 'Revisar'
        row['detalle'] = '; '.join(issues)[:250]
    elif row['plugins_pendientes'] or row['temas_pendientes']:
        row['estado'] = 'Actualizaciones pendientes'
    else:
        row['estado'] = 'Sin actualizaciones reportadas'
    return row

def write_html(rows, output):
    headers = ['ruta', 'estado', 'version_wp', 'plugins_pendientes', 'temas_pendientes', 'detalle']
    body = '\n'.join('<tr>' + ''.join('<td>' + html.escape(str(r[h])) + '</td>' for h in headers) + '</tr>' for r in rows)
    page = '''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>WP Fleet Manager</title><style>body{font:16px system-ui,sans-serif;max-width:1200px;margin:40px auto;padding:0 20px;color:#242135;background:#faf9fc}h1{color:#674c9c}p{color:#655e70}table{border-collapse:collapse;width:100%;background:white}td,th{text-align:left;padding:12px;border:1px solid #e6e0ed;overflow-wrap:anywhere}th{background:#eae2f5}@media(max-width:700px){body{margin:15px}table{font-size:12px}}</style><h1>WP Fleet Manager</h1><p>Informe local de solo lectura. Contiene rutas internas: no publicar.</p><p>Instalaciones detectadas: ''' + str(len(rows)) + '''</p><table><thead><tr>''' + ''.join('<th>' + html.escape(h.replace('_',' ').title()) + '</th>' for h in headers) + '</tr></thead><tbody>' + body + '</tbody></table></html>'
    output.write_text(page, encoding='utf-8')

def main():
    p = argparse.ArgumentParser(description='Auditoría local y de solo lectura de WordPress bajo una ruta')
    p.add_argument('--root', required=True, help='Carpeta bajo la cual buscar WordPress (ej: /home/usuario/public_html)')
    p.add_argument('--depth', type=int, default=5, help='Profundidad máxima (por defecto 5)')
    p.add_argument('--max-sites', type=int, default=250, help='Máximo de instalaciones a revisar')
    p.add_argument('--timeout', type=int, default=15, help='Timeout WP-CLI por consulta, segundos')
    p.add_argument('--no-wpcli', action='store_true', help='Solo detectar instalaciones, sin ejecutar WP-CLI')
    p.add_argument('--output', default='wp-fleet-report', help='Prefijo de los informes CSV/HTML')
    args = p.parse_args()
    if args.depth < 0 or not (1 <= args.max_sites <= 10000) or not (1 <= args.timeout <= 300):
        p.error('depth >= 0, max-sites 1..10000 y timeout 1..300')
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        p.error('La ruta --root no es una carpeta accesible')
    if hasattr(os, 'geteuid') and os.geteuid() == 0:
        p.error('No ejecutar como root; usa la cuenta propietaria de los WordPress')
    paths = discover(root, args.depth, args.max_sites)
    wpcli = shutil.which('wp') is not None and not args.no_wpcli
    print(f'Detectados: {len(paths)} WordPress | WP-CLI: {"sí" if wpcli else "no"}')
    rows = []
    for index, path in enumerate(paths, 1):
        print(f'[{index}/{len(paths)}] {path}', flush=True)
        rows.append(audit(path, wpcli, args.timeout))
    prefix = Path(args.output).expanduser()
    prefix.parent.mkdir(parents=True, exist_ok=True)
    fields = ['ruta', 'estado', 'version_wp', 'plugins_pendientes', 'temas_pendientes', 'detalle']
    with prefix.with_suffix('.csv').open('w', newline='', encoding='utf-8-sig') as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    write_html(rows, prefix.with_suffix('.html'))
    print(f'Informes: {prefix.with_suffix(".csv")} | {prefix.with_suffix(".html")}')
    print('ATENCIÓN: incluyen rutas internas. No compartir públicamente sin anonimizar.')

if __name__ == '__main__':
    main()
