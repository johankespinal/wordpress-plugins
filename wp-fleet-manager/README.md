# WP Fleet Manager

Inventario **de solo lectura** para numerosas instalaciones WordPress de una cuenta cPanel / SSH.

Escanea carpetas buscando instalaciones WordPress y, si WP-CLI está disponible, comprueba la versión del núcleo y actualizaciones pendientes de plugins y temas. Produce informes HTML y CSV. No actualiza ni elimina archivos.

## Requisitos

Python 3.8+, acceso al sistema de archivos propio de la cuenta y, opcionalmente, WP-CLI instalado. Ejecutar **como usuario de cPanel, nunca como root**.

## Uso

```bash
# Inventario sin ejecutar WordPress
python3 wp_fleet.py --root "$HOME/public_html" --no-wpcli

# Auditoría con WP-CLI cuando sea seguro
python3 wp_fleet.py --root "$HOME" --depth 5 --output "$HOME/wp-fleet-report"

python3 wp_fleet.py --help
```

**Importante:** guarda informes fuera de `public_html`; contienen rutas internas y no deben subirse públicamente. WP-CLI con `--skip-plugins --skip-themes` aún puede ejecutar código de mu-plugins o arranque; en instalaciones sospechosas utiliza `--no-wpcli`.

**Estado:** versión inicial, pendiente de pruebas en entornos de hosting reales.
