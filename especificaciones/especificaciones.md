Proyecto Prospección - Gálvez SpA
1. Visión General del Proyecto
Objetivo: Desarrollar una aplicación web colaborativa que automatice la compilación, análisis y generación de informes técnicos de prospección geológico-minera y propiedad minera en Chile. La herramienta debe estandarizar reportes (orientados a pequeña minería y evaluación ENAMI), cruzando datos espaciales, legales y de laboratorio.
Stack Tecnológico Requerido: Python, Streamlit (Frontend/UI), PyProj (Geometría), GeoPandas/PyQGIS (GIS), pdfplumber/Camelot (Extracción PDF), Requests (APIs), ReportLab o FPDF (Generación PDF).

2. Identidad Visual y UI/UX
Nombre de la App: Proyecto Prospección (Marca asociada: LOROS).

Empresa: Gálvez SpA.

Estilo Visual: Tema oscuro (Dark Mode), estilo industrial. Fondo gris pizarra/oscuro (#1e1e1e), con textos en blanco/gris claro y botones de acento corporativo (dorado/naranja extraído del logo a color).

Logos: * Logos_Galvez_Spa_color.jpg: Panel principal y portada del informe.

Logos_Galvez_Spa_blanco.jpg: Fondos oscuros o pies de página.

Interfaz: Basada en Streamlit. Sidebar lateral para controles e inputs; Panel central dinámico para previsualización de datos, mapas y tablas.

3. Especificaciones de Módulos (Core Features)
Módulo 1: Autenticación y Acceso (Login)
Sistema de login básico en la pantalla de inicio para restringir el acceso solo a colaboradores autorizados del equipo.

Almacenamiento de sesión (st.session_state) para registrar qué usuario está operando la herramienta.

Módulo 2: Ingesta y Transformación Dinámica de Coordenadas
Problema: Los datos de terreno provienen de distintas fuentes.

Solución: Un selector (Radio button) que permita ingresar coordenadas en 3 formatos:

UTM PSAD56 (Huso 19S) - EPSG:24879

UTM WGS84 (Huso 19S) - EPSG:32719

Latitud / Longitud (Grados decimales, WGS84) - EPSG:4326

Acción del Backend: Independiente del input, usar la librería pyproj para normalizar temporalmente las coordenadas a WGS84 (para integraciones web/APIs) y a la proyección del shapefile local (para cruce de datos).

Módulo 3: Integración Legal (Catastro Sernageomin)
Objetivo: Obtener datos legales de la concesión minera que intersecta con la coordenada ingresada.

Acción: Realizar peticiones (vía API REST o WFS) al servidor de Sernageomin (https://appsngmaz.sernageomin.cl/catastro_SNGM/home/index).

Outputs esperados: Nombre de concesión, Rol Nacional, Titular, Estado, Hectáreas y la geometría del polígono para graficarlo sobre el mapa base (Satelital).

Módulo 4: Procesamiento Geológico Espacial (Offline/Local)
Objetivo: Extraer el contexto geológico sin depender de internet.

Inputs: Archivos locales del mapa geológico de Chile (mapa geo chile.shp, .dbf, .shx, .prj) y la base de datos tabla de atributos.xlsx - geologia_chile_interactiva_1__g.csv.

Acción: Usar GeoPandas para realizar una intersección espacial (Point in Polygon) entre la coordenada del usuario y el shapefile.

Outputs esperados: Extraer atributos de la roca (Edad, Unidad, Lito, Símbolo) correspondientes a ese punto exacto, y exportar un recorte del mapa (JPG/PNG) centrado en la faena para incluir en el PDF.

Módulo 5: Extracción Dinámica de Laboratorios (OCR/PDF Parsing)
Objetivo: Leer resultados de laboratorio (ej. F.G.F. Análisis Mineros) sin intervención manual.

Restricción Crítica: NO debe estar "hardcodeado" solo para Oro (Au). Debe ser dinámico.

Acción: Procesar archivos PDF o Excel mediante "Drag & Drop". Leer las tablas y detectar los encabezados dinámicamente (ej. Au, Cu, Ag, Mo, Retallas, Fino, Grueso).

Outputs esperados: Un DataFrame limpio (pandas) renderizado en la interfaz web para validación del usuario, listo para inyectarse en el PDF final.

Módulo 6: Motor de Interpretación (LLM/IA Placeholder)
Objetivo: Cruzar datos del Módulo 4 (Geología) con el Módulo 5 (Leyes del Laboratorio).

Acción: Preparar un prompt estructurado (ej. "Muestras con Cu 2.5% en Intrusivos Ki2c...") que será procesado por un modelo de lenguaje (representando el conocimiento curado de NotebookLM) para autocompletar un campo de texto en la UI con conclusiones y recomendaciones preliminares (ej. recomendación de molienda o gravimetría por efecto pepita). El usuario debe poder editar este texto.

Módulo 7: Generador del Informe Final (PDF Export)
Objetivo: Compilar todo en un documento estandarizado.

Acción: Usar un generador de PDF para emular la estructura de los ejemplos (FRANCISCO PEREZ_merged.pdf, etc.).

Estructura del PDF:

Portada con mapa satelital + Logo Gálvez SpA.

Introducción geológica dinámica (inyectada del Módulo 4).

Rutas y Accesos.

Propiedad Minera (Datos del Módulo 3 + Mapa Sernageomin).

Contexto Geológico (Mapa local + edades).

Resultados e Interpretación (Tabla Módulo 5 + Texto Módulo 6).

Anexos: Inserción de las páginas de los PDFs originales de laboratorio al final del reporte.

Instrucciones para el Agente de Antigravity
Analiza este documento por completo antes de ejecutar comandos.

Crea el entorno virtual e instala las dependencias clave.

Comienza desarrollando el Módulo 1 y Módulo 2 en app.py para establecer la interfaz base en Streamlit. Asegura que el cambio de formato de coordenadas actualice la UI correctamente.

No avances al procesamiento de Shapefiles o generación de PDF hasta que la interfaz base, el ruteo de archivos locales y la transformación de coordenadas (PyProj) funcionen sin errores y sean aprobadas por el usuario.

