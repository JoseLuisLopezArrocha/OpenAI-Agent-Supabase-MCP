# Guía de Uso: AgenteSupabaseAI (OpenAI Agents SDK)

Este proyecto utiliza el SDK `openai-agents` para crear un **Agente Autónomo de Base de Datos** capaz de administrar Supabase (crear proyectos, tablas y datos) usando lenguaje natural.

## 1. Instalación y Dependencias

El proyecto ya incluye un `requirements.txt`. Instala todo con:

```powershell
pip install -r requirements.txt
```

Esto instalará:
*   `openai-agents`: El motor del agente.
*   `supabase`: Cliente oficial para operaciones de datos (CRUD).
*   `psycopg2`: Driver PostgreSQL para operaciones administrativas (DDL).
*   `python-dotenv`: Para cargar secretos desde `.env`.
*   `requests`: Para la Management API.

## 2. Cómo funciona el Agente

El archivo principal es `agent.py`. Define un agente con las siguientes capacidades (Herramientas):

### A. Gestión de Proyectos (Supabase Management API)
*   **Listar Proyectos**: Ve todos tus proyectos de Supabase.
*   **Crear Proyecto**: Crea una nueva base de datos/proyecto (por defecto en `eu-west-1`).
*   **Seleccionar Proyecto**: Configura el agente para trabajar sobre un proyecto específico.

### B. Administración de Base de Datos (SQL Directo)
Conecta al puerto 5432 de Postgres usando `psycopg2`.
*   **`ejecutar_sql_admin`**: Permite al agente ejecutar `CREATE TABLE`, `DROP TABLE`, `ALTER`, etc.
*   *Nota*: Requiere la contraseña de base de datos (`DB_PASSWORD` en `.env`).

### C. Operaciones de Datos (Supabase Client)
Conecta vía API REST (HTTPS) usando la librería `supabase`.
*   **`consultar_base_datos`**: Hace `SELECT` sobre tablas.
*   **`insertar_registro`**: Hace `INSERT` into tablas.

## 3. Configuración del Modelo (Local vs Nube)

Al iniciar `agent.py`, verás un menú de selección:

1.  **Servidor Local (Ollama)**: Ideal para privacidad y coste cero.
    *   Requiere tener Ollama corriendo (`ollama serve`).
    *   Usa `http://localhost:11434/v1`.
2.  **Gemini Flash / Pro**: Usa modelos de Google (gratuitos/rápidos) simulando ser OpenAI.
    *   Requiere una API Key de Google AI Studio.

## 4. Estructura del Código

```text
/
├── agent.py                 # Punto de entrada. Define el Agente y Tools.
├── supabase_manager.py      # Clase auxiliar para la API de Gestión de Supabase.
├── .env                     # (No incluido en git) Tus secretos.
├── requirements.txt         # Dependencias.
└── diagnostico/
    └── full_lifecycle_test.py  # Script CLI para validar conexión y ciclo de vida.
```

## 5. Diagnóstico

Si tienes problemas de conexión (especialmente DNS en proyectos nuevos), usa la herramienta de diagnóstico incluida:

```powershell
python diagnostico/full_lifecycle_test.py
```

Te permitirá probar aisladamente la creación, conexión a datos y borrado de proyectos.
