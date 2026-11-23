# WordPress Tools · Johan K. Espinal

Herramientas públicas para administrar WordPress, realizar auditorías y simplificar tareas técnicas de SEO y hosting.

> **Importante:** actualmente son **scripts independientes en Python**, no plugins PHP instalables desde el panel de WordPress. Mantengo el nombre `wordpress-plugins` como espacio del proyecto; la documentación de cada herramienta indica su modo de ejecución.

## Herramientas

| Proyecto | Función | Tecnología |
| --- | --- | --- |
| [WP Fleet Manager](wp-fleet-manager/README.md) | Inventario y revisión de numerosas instalaciones WordPress en una cuenta cPanel/SSH. | Python · WP-CLI opcional |
| [Redirect Detective](redirect-detective/README.md) | Audita cadenas de redirecciones, bucles, HTTP y destinos desde una lista de URL. | Python · HTTP |
| [Migration Preflight](migration-preflight/README.md) | Revisión de archivos, componentes y espacio disponible antes de migrar WordPress. | Python · sistema de archivos |

## Inicio rápido

```bash
# Inventario básico: solo lectura, sin ejecutar código WordPress
python3 wp-fleet-manager/wp_fleet.py --root "$HOME/public_html" --no-wpcli

# Analiza una lista de URL públicas
python3 redirect-detective/redirect_detective.py urls.txt --output redirect-report.csv

# Revisión previa de una instalación antes de migrarla
python3 migration-preflight/migration_preflight.py --path "$HOME/public_html" --output "$HOME/preflight"
```

## Seguridad, privacidad y alcance

- Herramientas de **diagnóstico**. No actualizan ni eliminan plugins, archivos, bases de datos o sitios.
- Ejecutarlas únicamente sobre instalaciones propias o administradas con autorización.
- Evitar trabajar como root; usar la cuenta de hosting autorizada.
- Los informes pueden contener rutas y URL sensibles: **no subirlos al repositorio**.
- WP Fleet Manager y Migration Preflight no son herramientas de eliminación de malware.
- Redirection Detective envía solicitudes HTTP a los sitios de la lista: leer sus restricciones de red antes de utilizar.
- **Estado:** versiones iniciales 0.1; pendientes de pruebas integrales sobre entornos reales.

## En desarrollo

Además de herramientas Python, este repositorio podrá incluir plugins PHP para WordPress con estructura estándar, activación y desinstalación seguras. Esos proyectos estarán claramente identificados como plugins instalables.

**Autor:** Johan K. Espinal · [Perfil](https://github.com/johankespinal) · [Sitio web](https://webseodigital.es/)
