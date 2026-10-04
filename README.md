# Sitio Parada KM1 / KM1 Capital (maqueta)

- `src/` fuente: `styles.css`, `main.js`, `pages/*.html` (contenido por página)
- `assets/` logo e imágenes de referencia recortadas del manual de identidad
- `build.py` genera `dist/` (sitio estático multipágina para `public_html`) y `preview.html` (vista previa de un archivo)
- `python3 build.py` para regenerar

Formularios: solo front-end. Al enviar muestran confirmación y guardan el prospecto en el navegador
(localStorage) para la demo de `panel.html`. Falta conectar CRM/backend, aviso de privacidad final y versión en inglés.
