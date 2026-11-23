#!/usr/bin/env python3
"""Migration Preflight: comprobaciones locales antes de migrar WordPress (solo lectura)."""
import argparse
import csv
import html
import json
import os
import shutil
import subprocess
from pathlib import Path

EXCLUDE = {'.git', 'node_modules', 'vendor', '.cache'}
def bytes_human(n):
    for unit in ['B','KB','MB','GB','TB']:
        if n < 1024:
            return f'{n:.1f} {unit}'
        n /= 1024
    return f'{n:.1f} PB'

def collect(root, max_files):
    n, total, big, links, errors = 0, 0, [], 0, []
    for base, dirs, files in os.walk(root, followlinks=False):
        here = Path(base)
        dirs[:] = [x for x in dirs if x not in EXCLUDE and not (here/x).is_symlink()]
        for name in files:
            p = here / name
            if p.is_symlink():
                links += 1
                continue
            try:
                st = p.stat()
                total += st.st_size
                n += 1
                if st.st_size >= 100 * 1024 * 1024:
                    big.append((st.st_size, str(p.relative_to(root))))
            except OSError as e:
                errors.append(str(p.relative_to(root)) + ': ' + str(e)[:80])
            if n >= max_files:
                return n, total, big, links, errors, True
    return n, total, big, links, errors, False

def php_info():
    if not shutil.which('php'):
        return {'php_cli': 'No disponible'}
    try:
        p = subprocess.run(['php', '-v'], capture_output=True, text=True, timeout=6)
        return {'php_cli': p.stdout.splitlines()[0] if p.returncode == 0 and p.stdout else 'No se pudo consultar'}
    except (OSError, subprocess.TimeoutExpired):
        return {'php_cli': 'Error de consulta'}

def main():
    ap = argparse.ArgumentParser(description='Checklist local de WordPress antes de migración: solo lectura')
    ap.add_argument('--path', required=True, help='Carpeta raíz de la instalación WordPress')
    ap.add_argument('--output', default='migration-preflight', help='Prefijo del informe JSON y HTML')
    ap.add_argument('--max-files', type=int, default=200000)
    ap.add_argument('--show-large', type=int, default=20)
    args = ap.parse_args()
    if args.max_files < 1 or not 0 <= args.show_large <= 100:
        ap.error('max-files debe ser >=1 y show-large debe estar entre 0 y 100')
    root = Path(args.path).expanduser().resolve()
    if not root.is_dir():
        ap.error('La ruta indicada no existe o no es accesible')
    if hasattr(os, 'geteuid') and os.geteuid() == 0:
        ap.error('Ejecuta la herramienta con el usuario de la cuenta, no como root')
    required = ['wp-config.php', 'wp-admin', 'wp-includes', 'wp-content', 'index.php']
    checks = {name: (root / name).exists() for name in required}
    n, size, large, links, errors, limited = collect(root, args.max_files)
    try:
        disk = shutil.disk_usage(root)
        free = disk.free
    except OSError:
        free = None
    report = {
        'path': str(root),
        'checks': checks,
        'files_count': n,
        'files_bytes': size,
        'files_human': bytes_human(size),
        'scan_limited': limited,
        'symlinks_skipped': links,
        'disk_free_bytes': free,
        'disk_free_human': bytes_human(free) if free is not None else 'No disponible',
        'php': php_info(),
        'largest_files_over_100mb': [{'size_bytes': sz, 'path': p} for sz,p in sorted(large,reverse=True)[:args.show_large]],
        'errors': errors[:100],
        'notes': [
            'PHP CLI puede diferir de la versión PHP configurada para el dominio',
            'No verifica acceso a MySQL, dumps de bases de datos, DNS, licencias ni compatibilidad del destino',
            'El tamaño contabilizado no incluye el contenido de la base de datos',
            'Los informes contienen rutas internas: conservarlos fuera del directorio web',
        ]
    }
    prefix = Path(args.output).expanduser()
    prefix.parent.mkdir(parents=True, exist_ok=True)
    json_file = prefix.with_suffix('.json')
    json_file.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    rows = [('Directorio',str(root)),('Archivos contados',str(n)),('Tamaño archivos',report['files_human']),
            ('Escaneo incompleto','Sí' if limited else 'No'),('Enlaces simbólicos omitidos',str(links)),
            ('Espacio libre',report['disk_free_human']),('PHP de consola',report['php']['php_cli'])]
    rows.extend((name, 'Presente' if exists else 'FALTA') for name,exists in checks.items())
    rows_html = ''.join('<tr><th>'+html.escape(k)+'</th><td>'+html.escape(v)+'</td></tr>' for k,v in rows)
    notes = ''.join('<li>'+html.escape(n)+'</li>' for n in report['notes'])
    page = ('<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
            '<title>Migration Preflight</title><style>body{max-width:900px;margin:35px auto;padding:15px;font:16px system-ui;background:#faf9fc;color:#282335}h1{color:#7255a9}table{border-collapse:collapse;width:100%;background:#fff}td,th{padding:12px;border:1px solid #e7e2ef;text-align:left;overflow-wrap:anywhere}</style>'
            '<h1>Migration Preflight</h1><p>Evaluación local de solo lectura antes de una migración WordPress.</p>'
            '<table>'+rows_html+'</table><h2>Limitaciones</h2><ul>'+notes+'</ul></html>')
    prefix.with_suffix('.html').write_text(page,encoding='utf-8')
    print('Archivos:',n,'| Tamaño:',report['files_human'])
    print('Informes:',json_file,'y',prefix.with_suffix('.html'))
    if limited:
        print('ATENCIÓN: escaneo truncado por --max-files; estimación de tamaño incompleta.')
    if not all(checks.values()):
        print('ATENCIÓN: faltan componentes habituales de WordPress.')
    print('No se ha modificado ninguna instalación.')

if __name__ == '__main__':
    main()
