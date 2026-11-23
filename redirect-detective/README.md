# Redirect Detective

Comando gratuito para **auditar redirecciones SEO** desde un listado de direcciones web públicas.

Identifica: respuesta HTTP, destino final, número de saltos, cadenas de redirección, bucles y errores. Exporta CSV.

## Requisitos

Python 3.8+; no necesita paquetes externos.

## Uso

Crea `urls.txt` con una URL HTTP/HTTPS por línea:

```text
https://example.org/
https://example.org/antigua-pagina
```

Ejecuta:

```bash
python3 redirect_detective.py urls.txt --output reporte.csv
```

Opciones: `--timeout 8 --max-hops 8 --max-urls 500`.

## Privacidad y seguridad

- Diseñado para **URLs públicas**, no para auditar intranets, localhost ni servicios con puertos privados.
- Revisa los destinos de los saltos, bloquea direcciones IP no públicas y limita la longitud de la cadena. **No garantiza aislamiento de red frente a cambios DNS (DNS rebinding)**; utiliza el script solo en un entorno de confianza y con listados conocidos.
- Las URL introducidas provocan solicitudes de red; evita credenciales y datos personales en sus parámetros.
- Utiliza HEAD y recurre a GET si el servidor devuelve 405 o 501. GET podría tener efectos secundarios en servidores mal configurados.
- No modifica tus WordPress ni tus servidores.
- No es un rastreador integral ni realiza auditoría de enlaces internos o canonicals.

**Estado:** MVP 0.1, pendiente de pruebas de integración con sitios reales. **Autor:** Johan K. Espinal.
