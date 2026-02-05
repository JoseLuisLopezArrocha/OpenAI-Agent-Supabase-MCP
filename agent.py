"""
==============================================
AgenteSupabaseAI - Agente Principal
==============================================
Agente autónomo de base de datos impulsado por LLMs.
Permite administrar proyectos de Supabase, crear esquemas SQL
y manipular datos mediante lenguaje natural.

Uso:
    python agent.py

Autor: JoseLuisLopezArrocha
Licencia: MIT
==============================================
"""

import os
import json
import asyncio
import psycopg2
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool
from supabase import create_client, Client
from supabase_manager import SupabaseManager

# ==============================================
# CONFIGURACIÓN
# ==============================================

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración Global
SUPABASE_ACCESS_TOKEN = os.getenv("SUPABASE_ACCESS_TOKEN")
DB_PASSWORD = os.getenv("DB_PASSWORD") # Necesario para Admin SQL y Crear Proyectos
SUPABASE_POOLER_HOST = os.getenv("SUPABASE_POOLER_HOST") # Host del pooler (IPv4 compatible)

# Configuración OpenAI / Modelo
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1") 
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "ollama") 
MODEL_NAME = os.getenv("MODEL_NAME", "glm-4.7-flash:latest")

# --- Estado Global del Agente ---
# Almacena el contexto del proyecto seleccionado actualmente
active_project = {
    "ref": None,
    "url": None,
    "anon_key": None,
    "service_key": None,
    "db_host": None,      # Ahora usa el pooler
    "db_user": "postgres", # Formato: postgres.{ref} para pooler
    "db_port": "5432"      # Puerto del pooler
}

manager: SupabaseManager = None
supabase_client: Client = None

# --- Herramientas de Gestión de Proyectos ---

@function_tool
async def listar_proyectos() -> str:
    """
    Lista todos los proyectos de Supabase disponibles en la cuenta.
    Devuelve ID, Nombre, Región y Estado.
    """
    try:
        proyectos = manager.list_projects()
        # Simplificar output para el agente
        resumen = []
        for p in proyectos:
            resumen.append({
                "id": p['id'],
                "name": p['name'],
                "status": p['status'],
                "region": p['region']
            })
        return json.dumps(resumen, indent=2)
    except Exception as e:
        return f"Error listando proyectos: {e}"

@function_tool
async def crear_proyecto(nombre: str) -> str:
    """
    Crea un nuevo proyecto (Base de Datos) en Supabase.
    Requiere que el nombre sea único.
    Toma unos minutos en estar listo.
    """
    if not DB_PASSWORD:
        return "Error: No se ha configurado DB_PASSWORD en el entorno."
        
    try:
        print(f"[Tool] Creando proyecto '{nombre}'...")
        # Usamos la contraseña global del entorno
        proyecto = manager.create_project(nombre, DB_PASSWORD)
        return f"Proyecto '{nombre}' creado exitosamente. ID: {proyecto['id']}. Estado inicial: {proyecto['status']}. Espera unos minutos antes de usarlo."
    except Exception as e:
        return f"Error creando proyecto: {e}"

@function_tool
async def seleccionar_proyecto(project_ref: str) -> str:
    """
    Selecciona un proyecto para trabajar.
    Configura internamente las credenciales para consultar DB y ejecutar Admin SQL.
    Debe llamarse antes de intentar consultar o modificar la base de datos.
    """
    global active_project, supabase_client
    
    print(f"[Tool] Seleccionando proyecto {project_ref}...")
    try:
        # 1. Obtener Keys
        keys = manager.get_project_api_keys(project_ref)
        anon = keys.get("anon")
        service = keys.get("service_role")
        
        if not anon or not service:
            return "Error: No se pudieron recuperar las API KEYS del proyecto."

        # 2. Configurar URLs
        url = f"https://{project_ref}.supabase.co"
        
        # 3. Determinar host del pooler
        # Prioridad: Variable de entorno > Patrón por defecto
        if SUPABASE_POOLER_HOST:
            db_host = SUPABASE_POOLER_HOST
            print(f"[Tool] Usando pooler desde .env: {db_host}")
        else:
            # Fallback: construir patrón por defecto (puede no funcionar en todos los casos)
            projects = manager.list_projects()
            region = "eu-west-1"
            for p in projects:
                if p['id'] == project_ref:
                    region = p.get('region', 'eu-west-1')
                    break
            db_host = f"aws-1-{region}.pooler.supabase.com"
            print(f"[Tool] ⚠️ SUPABASE_POOLER_HOST no configurado. Usando patrón por defecto: {db_host}")
            print(f"[Tool] Si falla la conexión, configura SUPABASE_POOLER_HOST en .env (ver README)")
        
        # 4. Actualizar estado global - Usar Pooler (Supavisor) para IPv4
        active_project["ref"] = project_ref
        active_project["url"] = url
        active_project["anon_key"] = anon
        active_project["service_key"] = service
        active_project["db_host"] = db_host
        active_project["db_user"] = f"postgres.{project_ref}"
        
        # 5. Inicializar cliente Supabase (para Data API)
        supabase_client = create_client(url, service) # Usamos service role para poder escribir sin RLS si es necesario
        
        return f"Proyecto {project_ref} seleccionado. Cliente configurado. Host Pooler: {active_project['db_host']}"
        
    except Exception as e:
        return f"Error seleccionando proyecto: {e}"

# --- Herramientas de Base de Datos (Contexto Activo) ---

def _check_context():
    if not active_project["ref"]:
        raise Exception("No hay proyecto seleccionado. Usa 'listar_proyectos' y luego 'seleccionar_proyecto'.")

@function_tool
async def consultar_base_datos(tabla: str, query: str = None) -> str:
    """
    Consulta la base de datos del proyecto ACTIVO usando la API REST.
    """
    try:
        _check_context()
        print(f"[Tool] Consultando tabla '{tabla}' en {active_project['ref']}...")
        response = supabase_client.table(tabla).select("*").execute()
        return json.dumps(response.data)
    except Exception as e:
        return f"Error consultando DB: {e}"

@function_tool
async def insertar_registro(tabla: str, datos: str) -> str:
    """
    Inserta un registro en la base de datos del proyecto ACTIVO.
    'datos' debe ser un JSON string válido.
    """
    try:
        _check_context()
        print(f"[Tool] Insertando en '{tabla}': {datos}")
        data_dict = json.loads(datos)
        response = supabase_client.table(tabla).insert(data_dict).execute()
        return json.dumps(response.data)
    except Exception as e:
        return f"Error insertando en DB: {e}"

@function_tool
async def ejecutar_sql_admin(sql: str) -> str:
    """
    Ejecuta SQL arbitrario (DDL/DML) con privilegios de administrador (postgres user).
    Usa la conexión directa PostgreSQL al proyecto ACTIVO.
    """
    try:
        _check_context()
        
        if not DB_PASSWORD:
            return "Error: DB_PASSWORD no configurada en entorno."

        print(f"[Tool Admin] Ejecutando SQL via Pooler en {active_project['db_host']}: {sql}")
        
        # Conexión via Supabase Pooler (Supavisor) - soporta IPv4
        conn = psycopg2.connect(
            host=active_project["db_host"],
            database="postgres",
            user=active_project["db_user"],  # postgres.{ref} para pooler
            password=DB_PASSWORD,
            port=active_project["db_port"]
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        cursor.execute(sql)
        
        resultado = "SQL Ejecutado Correctamente"
        if cursor.description:
            rows = cursor.fetchall()
            columnas = [desc[0] for desc in cursor.description]
            lista_dicts = [dict(zip(columnas, row)) for row in rows]
            resultado = json.dumps(lista_dicts, default=str)
            
        cursor.close()
        conn.close()
        return resultado
        
    except Exception as e:
        return f"Error ejecutando SQL Admin: {e}"

# --- Main ---

async def main():
    global manager
    
    # 0. Validar Entorno
    if not SUPABASE_ACCESS_TOKEN:
        print("❌ Error: SUPABASE_ACCESS_TOKEN no encontrado en .env")
        exit(1)
        
    # 1. Inicializar Manager
    manager = SupabaseManager(SUPABASE_ACCESS_TOKEN)
    
    # 2. Configurar Agente (Solo Local)
    # Aseguramos que el entorno tenga las variables que espera el SDK/LangChain
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
    os.environ["OPENAI_BASE_URL"] = OPENAI_BASE_URL
    os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"
    
    agent = Agent(
        name="SupabaseMaster",
        instructions=(
            "Eres un experto administrador de Supabase. "
            "Tu flujo de trabajo usual es: LISTAR proyectos, SELECCIONAR uno, y luego administrarlo. "
            "Si te piden crear algo nuevo, usa 'crear_proyecto', pero recuerda que tarda minutos en provisionarse. "
            "Para crear tablas, usa 'ejecutar_sql_admin' DESPUÉS de haber seleccionado un proyecto. "
            "Si el usuario te da instrucciones vagas, asume que se refiere al proyecto seleccionado si ya hay uno."
        ),
        model=MODEL_NAME,
        tools=[
            listar_proyectos, 
            crear_proyecto, 
            seleccionar_proyecto, 
            consultar_base_datos, 
            insertar_registro, 
            ejecutar_sql_admin
        ]
    )

    print(f"\nAgente Supabase Master iniciado ({MODEL_NAME}).")
    print("Modo: Servidor Local Zonzamas")
    print("Comandos: 'salir' para terminar.")
    
    while True:
        try:
            user_input = input("\nUsuario: ")
            if user_input.lower() in ["salir", "exit"]:
                break
            
            result = await Runner.run(agent, user_input)
            print(f"Asistente: {result.final_output}")
            
        except Exception as e:
            print(f"Error en loop: {e}")

if __name__ == "__main__":
    asyncio.run(main())
