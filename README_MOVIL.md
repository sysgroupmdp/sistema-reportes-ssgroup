# S&S Group Reportes — versión móvil

Esta versión adapta la app para uso cómodo desde Samsung, iPhone, Mac y PC.

## Cambios incluidos
- Interfaz responsive para pantalla chica.
- Botones grandes y campos optimizados para celular.
- Cámara directa desde el navegador (`st.camera_input`).
- Alternativa para elegir una foto de la galería.
- Selección de cliente guardado con autocompletado.
- Selección de obra guardada filtrada por cliente con autocompletado.
- Eliminación individual de hallazgos antes de generar el PDF.
- Botón persistente para descargar/compartir el último PDF generado.
- Se conserva la base SQLite, clientes, obras, recomendaciones, historial y PDFs existentes.

## Ejecutar localmente
1. Instalar Python 3.10 o superior.
2. En Terminal, ubicarse en esta carpeta.
3. Ejecutar: `pip install -r requirements.txt`
4. Ejecutar: `streamlit run app.py`

## Uso desde el celular en la misma red Wi‑Fi
Con la app corriendo en la Mac/PC, usar la dirección de red que muestra Streamlit (Network URL) desde Chrome/Safari del celular.

## Publicación online
La app puede publicarse en Streamlit Community Cloud desde GitHub. Importante: el disco de Streamlit Cloud no debe considerarse almacenamiento permanente para SQLite, fotos o PDFs. Para una versión de producción con clientes/historial persistentes conviene migrar esos datos a un servicio persistente (por ejemplo Supabase/PostgreSQL) antes de depender del sistema como archivo definitivo.
