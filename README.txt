STUDYGO WEB — PROTOTIPO FULL-STACK

Requisitos: Python 3.10 o posterior.

Ejecución local:
1. Descomprimir el ZIP.
2. Abrir una terminal dentro de la carpeta StudyGO_Web_Completo.
3. Ejecutar: python -m venv .venv
4. Activar el entorno:
   Windows: .venv\Scripts\activate
   macOS/Linux: source .venv/bin/activate
5. Instalar dependencias: pip install -r requirements.txt
6. Ejecutar: python app.py
7. Abrir http://127.0.0.1:5000

Incluye:
- Registro e inicio/cierre de sesión.
- Contraseñas almacenadas como hash.
- Base de datos SQLite local.
- Perfil personalizable por usuario.
- Crear, completar y eliminar tareas.
- Crear eventos del calendario.
- Notificaciones dentro de la aplicación.
- Colores personalizados.
- Diseño adaptable a celular.

LÍMITES IMPORTANTES:
- Este es un prototipo para ejecución local, no está publicado en internet.
- Para publicar en producción se necesita configurar una clave secreta segura, HTTPS, copias de seguridad, protección contra abuso, políticas de privacidad y un servidor de despliegue.
- Las notificaciones son internas a la aplicación; no envía SMS, correo ni notificaciones push.
- El horario y la cuadrícula de calendario visual son ejemplos iniciales.
- Si lo usan alumnos reales, especialmente menores, coordinar autorización institucional y tratamiento adecuado de datos personales.
