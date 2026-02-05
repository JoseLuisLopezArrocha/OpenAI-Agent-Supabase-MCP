# OpenAI Agent + Supabase + MCP 🤖⚡

Un **Agente Autónomo de Base de Datos** impulsado por LLMs (Ollama/OpenAI) capaz de administrar proyectos de Supabase, crear esquemas SQL y manipular datos mediante lenguaje natural.

Este proyecto utiliza el SDK `openai-agents` y la API de Gestión de Supabase para ofrecer una experiencia "text-to-database" completa.

## 🚀 Características

*   **Gestión de Proyectos**: Crea y borra proyectos de Supabase (Bases de datos completas) desde el chat.
*   **Admin SQL**: Ejecuta comandos DDL (`CREATE TABLE`, etc.) conectándose directamente a Postgres (puerto 5432).
*   **CRUD de Datos**: Inserta, lee, actualiza y borra filas usando la API REST de Supabase.
*   **Agnóstico del Modelo**: Funciona con **Ollama** (Localmente) o con **Gemini/OpenAI** (en la nube).
*   **Robustez**: Incluye herramientas de diagnóstico para verificar conectividad y propagación DNS.

## 🛠️ Requisitos

*   Python 3.10+
*   Una cuenta de [Supabase](https://supabase.com) (necesitas un Personal Access Token).
*   (Opcional) [Ollama](https://ollama.com) instalado para uso local.

## 📦 Instalación

1.  **Clonar el repositorio**:
    ```bash
    git clone https://github.com/tu-usuario/AgenteSupabaseAI.git
    cd AgenteSupabaseAI
    ```

2.  **Instalar dependencias**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configurar Variables de Entorno**:
    Crea un archivo `.env` basado en `.env.example`:
    ```ini
    # .env
    SUPABASE_ACCESS_TOKEN=tu_token_personal_de_supabase_dashboard
    DB_PASSWORD=la_contraseña_que_quieres_para_tus_nuevas_bds
    
    # Opcional (si usas Gemini)
    OPENAI_API_KEY=tu_api_key
    ```

## ▶️ Uso

### 1. Iniciar el Agente
```bash
python agent.py
```
Selecciona tu proveedor de LLM (Ollama o OpenAI) en el menú interactivo y empieza a chatear.

**Ejemplos de comandos:**
*   _"Crea un proyecto nuevo llamado 'TiendaDemo'"_
*   _"En el proyecto TiendaDemo, crea una tabla 'productos' con id, nombre y precio"_
*   _"Inserta 5 productos de ejemplo"_
*   _"Borra el proyecto TiendaDemo"_

### 2. Diagnóstico y Pruebas
Si tienes problemas de conexión (común en proyectos recién creados por el DNS), usa el script de diagnóstico modular:

```bash
python diagnostico/full_lifecycle_test.py
```
Este script te guía paso a paso para Crear, Probar Datos y Borrar proyectos de forma controlada.

## 📄 Documentación Adicional

*   [Guía del SDK de Agentes](GUIA_OPENAI_AGENTS.md): Detalles técnicos sobre cómo extender el agente.

## ⚠️ Notas Importantes

*   **DNS Latency**: Al crear un proyecto nuevo, Supabase puede tardar 1-5 minutos en propagar el DNS (`db.xxx.supabase.co`). El agente tiene reintentos, pero a veces es necesario esperar.
*   **Región**: Por defecto, los proyectos se crean en `eu-west-1` (Irlanda). Puedes cambiarlo en `supabase_manager.py`.

## 🔧 Troubleshooting: Problema de Conexión IPv6

### Síntoma
Recibes errores como:
- `connection to server at "db.xxx.supabase.co" timeout expired`
- `Network is unreachable`
- Las pruebas de conexión fallan después de crear un proyecto

### Causa
Desde Enero 2024, Supabase solo asigna direcciones **IPv6** a las conexiones directas (`db.xxx.supabase.co`). Si tu ISP/router no soporta IPv6, no podrás conectar.

### Solución: Usar el Connection Pooler

1. **Obtén la URL del Pooler**:
   - Dashboard de Supabase → Tu proyecto → **Connect** (botón arriba)
   - Cambia "Method" de "Direct connection" a **"Session pooler"**
   - Copia el host (ej: `aws-1-eu-west-1.pooler.supabase.com`)

2. **Actualiza tu `.env`**:
   ```ini
   # Host del Connection Pooler (IPv4 compatible)
   SUPABASE_POOLER_HOST=aws-1-eu-west-1.pooler.supabase.com
   ```

3. El código usará automáticamente el pooler si está configurado.

### Formato de Conexión del Pooler
```
Host:     aws-1-{region}.pooler.supabase.com
Usuario:  postgres.{project_ref}
Puerto:   5432 (Session) o 6543 (Transaction)
```

> **Nota**: El prefijo del host (`aws-1`, `aws-0`, etc.) varía por proyecto y no se puede predecir. Siempre cópialo del Dashboard.

---
Creado con ❤️ y Python.
