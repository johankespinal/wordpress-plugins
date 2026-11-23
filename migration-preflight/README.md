# Migration Preflight

**Comprobación previa para migrar una instalación WordPress**, sin modificar ningún archivo.

Comprueba los componentes habituales de WordPress, cantidad y tamaño de los archivos, archivos grandes, espacio libre aproximado y versión de PHP **de consola**. Genera informes JSON y HTML.

## Requisitos

Python 3.8+. No requiere dependencias externas ni acceso a bases de datos. Ejecutar como usuario normal de cPanel/SSH, no como root.

## Uso

```bash
python3 migration_preflight.py --path "$HOME/public_html" --output "$HOME/migration-check"
```

Para instalaciones grandes: `--max-files 300000`.

## Qué NO hace

- No exporta ni copia WordPress, sus archivos o bases de datos.
- No confirma que el servidor de destino sea compatible.
- No verifica contenido, tamaño o acceso a MySQL.
- No comprueba la versión PHP utilizada por Apache/PHP-FPM; PHP CLI puede ser diferente.
- No cambia DNS, configuraciones, permisos ni bases de datos.
- No sustituye las pruebas de restauración ni la verificación final de una migración.

**Seguridad:** los informes pueden revelar rutas internas. Guárdalos **fuera de public_html** y no los subas a repositorios públicos.

**Estado:** MVP 0.1, pendiente de pruebas en servidores reales. **Autor:** Johan K. Espinal.
