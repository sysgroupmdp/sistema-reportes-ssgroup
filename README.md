
# S&S Group - Sistema de Reportes PDF V3

Sistema web local para navegador.

Incluye:
- Clientes guardados.
- Obras guardadas por cliente.
- Biblioteca de recomendaciones.
- Carga de hallazgos con foto.
- Exportación directa a PDF.
- Logo S&S Group en pantalla y en el PDF.
- Historial de reportes generados.
- Sin firma digital.

## Instalación en Mac

1. Abrir Terminal.
2. Ir a Descargas:

cd ~/Downloads

3. Descomprimir:

unzip sistema_reportes_pdf_ss_group_v3.zip

4. Entrar a la carpeta:

cd sistema_reportes_pdf_ss_group_v3

5. Instalar dependencias:

pip3 install -r requirements.txt

6. Ejecutar:

python3 -m streamlit run app.py

7. Abrir en navegador:

http://localhost:8501

## Importante

No borrar estos archivos/carpetas:
- ss_group_reportes.db
- uploads
- reportes_pdf

Ahí se guardan clientes, obras, fotos e historial.
