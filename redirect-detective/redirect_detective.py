#!/usr/bin/env python3
"""Redirect Detective: auditoría de redirecciones HTTP(S) con biblioteca estándar."""
import argparse
import csv
import html
import ipaddress
import socket
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

OPENER = urllib.request.build_opener(NoRedirect)
REDIRECTS = {301, 302, 303, 307, 308}

def safe_url(value):
    try:
        u = urllib.parse.urlsplit(value.strip())
        if u.scheme.lower() not in ('http', 'https') or not u.hostname or u.username or u.password:
            return False, 'URL no válida o con credenciales'
        if u.port is not None and u.port not in (80, 443):
            return False, 'Puerto no permitido (solo 80 y 443)'
        host = u.hostname
        if host.lower() == 'localhost' or host.lower().endswith(('.local', '.internal', '.localhost')):
            return False, 'Host local restringido'
        try:
            addrs = socket.getaddrinfo(host, u.port or (443 if u.scheme == 'https' else 80), type=socket.SOCK_STREAM)
        except OSError as e:
            return False, 'DNS no disponible: ' + str(e)[:100]
        if not addrs:
            return False, 'DNS sin direcciones'
        for addr in addrs:
            ip = ipaddress.ip_address(addr[4][0])
            if not ip.is_global:
                return False, 'IP no pública restringida'
        return True, ''
    except (ValueError, TypeError) as e:
        return False, 'URL inválida: ' + str(e)[:100]

def request_once(url, timeout):
    req = urllib.request.Request(url, headers={'User-Agent': 'RedirectDetective/0.1 (website audit)', 'Accept': '*/*'}, method='HEAD')
    try:
        with OPENER.open(req, timeout=timeout) as r:
            return r.status, r.headers.get('Location', '')
    except urllib.error.HTTPError as e:
        if e.code in (405, 501):
            # Algunos servidores no permiten HEAD; probar una petición GET limitada.
            req = urllib.request.Request(url, headers={'User-Agent': 'RedirectDetective/0.1 (website audit)'}, method='GET')
            try:
                with OPENER.open(req, timeout=timeout) as r:
                    return r.status, r.headers.get('Location', '')
            except urllib.error.HTTPError as e2:
                return e2.code, e2.headers.get('Location', '')
        return e.code, e.headers.get('Location', '')

def check(url, timeout=8, max_hops=8):
    original = url.strip()
    chain, seen = [], set()
    current = original
    for hop in range(max_hops + 1):
        ok, reason = safe_url(current)
        if not ok:
            return [original, current, 'BLOQUEADA', hop, ' | '.join(chain), reason]
        normalized = urllib.parse.urldefrag(current).url
        if normalized in seen:
            return [original, current, 'BUCLE', hop, ' | '.join(chain), 'Redirección circular']
        seen.add(normalized)
        try:
            code, location = request_once(current, timeout)
        except Exception as e:
            return [original, current, 'ERROR', hop, ' | '.join(chain), str(e)[:180]]
        chain.append(str(code) + ' ' + current)
        if code not in REDIRECTS:
            state = 'CORRECTA' if 200 <= code < 300 and hop == 0 else ('REDIRECCION' if 200 <= code < 300 else 'HTTP_' + str(code))
            if hop > 1 and state == 'REDIRECCION':
                state = 'CADENA_LARGA'
            return [original, current, state, hop, ' | '.join(chain), '']
        if not location:
            return [original, current, 'ERROR', hop, ' | '.join(chain), 'Redirección sin cabecera Location']
        current = urllib.parse.urljoin(current, location)
    return [original, current, 'LIMITE', max_hops, ' | '.join(chain), 'Superado el límite de redirecciones']

def main():
    p = argparse.ArgumentParser(description='Auditar redirecciones de URLs HTTP(S) públicas')
    p.add_argument('input', help='TXT con una URL por línea')
    p.add_argument('--output', default='redirect-report.csv', help='Archivo CSV resultante')
    p.add_argument('--timeout', type=float, default=8)
    p.add_argument('--max-hops', type=int, default=8)
    p.add_argument('--max-urls', type=int, default=500)
    a = p.parse_args()
    if not 0 < a.timeout <= 60 or not 0 < a.max_hops <= 20 or not 0 < a.max_urls <= 10000:
        p.error('timeout 0..60, max-hops 1..20, max-urls 1..10000')
    src = Path(a.input)
    if not src.is_file():
        p.error('No se encuentra el archivo de URLs')
    urls = [x.strip() for x in src.read_text(encoding='utf-8-sig').splitlines() if x.strip() and not x.lstrip().startswith('#')]
    if len(urls) > a.max_urls:
        p.error('Demasiadas URLs: aumenta --max-urls si es intencional')
    headers = ['url_original', 'url_final', 'estado', 'saltos', 'cadena', 'detalle']
    rows = []
    for i, url in enumerate(urls, 1):
        print(f'[{i}/{len(urls)}] {url}', flush=True)
        rows.append(check(url, a.timeout, a.max_hops))
    dest = Path(a.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)
    print('Informe guardado:', dest)

if __name__ == '__main__':
    main()
