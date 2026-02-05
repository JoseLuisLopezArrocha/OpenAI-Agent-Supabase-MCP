"""
==============================================
AgenteSupabaseAI - Test de Ciclo de Vida Completo
==============================================
Script interactivo para probar el ciclo de vida completo de proyectos:
- Crear proyectos
- Ejecutar pruebas de datos (DDL + CRUD)
- Eliminar proyectos

Uso:
    python diagnostico/full_lifecycle_test.py

Autor: JoseLuisLopezArrocha
Licencia: MIT
==============================================
"""

import sys
import os
import json
import time
import psycopg2
from supabase import create_client

# Añadir path raíz
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from dotenv import load_dotenv
from supabase_manager import SupabaseManager

load_dotenv(os.path.join(parent_dir, '.env'))

def print_step(title):
    print(f"\n🔹 --- {title} ---")

def wait_for_user(action):
    while True:
        resp = input(f"\n⏸️  {action} completada. Revisa en Supabase. Escribe 'C' para continuar: ")
        if resp.lower() == 'c':
            break

# --- MODULO 1: PRUEBAS DE DATOS (Conexión, TABLAS, CRUD) ---
def module_test_data():
    manager = SupabaseManager(os.getenv("SUPABASE_ACCESS_TOKEN"))
    projects = manager.list_projects()
    
    # Filtrar solo activos para evitar errores de DNS
    active_projects = [p for p in projects if p['status'] == 'ACTIVE_HEALTHY']
    
    if not active_projects:
        print("\n❌ No hay proyectos 'ACTIVE_HEALTHY' disponibles.")
        print("   Por favor, crea uno nuevo (Opción 1) y ESPECIFICA esperar unos minutos.")
        return

    print("\nProyectos Activos disponibles:")
    for idx, p in enumerate(active_projects):
        print(f"{idx + 1}. {p['name']} (ID: {p['id']})")
    
    try:
        sel = int(input("\nSelecciona el número del proyecto para probar: "))
        project = active_projects[sel - 1]
    except (ValueError, IndexError):
        print("Selección inválida.")
        return

    print_step(f"PRUEBA DE DATOS EN: {project['name']}")
    
    ref = project['id']
    print("Recuperando API Keys...")
    keys = manager.get_project_api_keys(ref)
    url = f"https://{ref}.supabase.co"
    
    # Usar Supabase Pooler (Supavisor) en lugar de conexión directa
    # El pooler soporta IPv4, evitando problemas de conectividad IPv6
    pooler_host = os.getenv("SUPABASE_POOLER_HOST")
    if pooler_host:
        db_host = pooler_host
        print(f"Usando pooler desde .env: {db_host}")
    else:
        # Fallback: construir patrón por defecto
        region = project.get('region', 'eu-west-1')
        db_host = f"aws-1-{region}.pooler.supabase.com"
        print(f"⚠️ SUPABASE_POOLER_HOST no configurado. Usando patrón: {db_host}")
        print("   Si falla, configura SUPABASE_POOLER_HOST en .env (ver README)")
    
    # El usuario del pooler incluye el project ref: postgres.{ref}
    db_user = f"postgres.{ref}"
    
    db_pass = os.getenv("DB_PASSWORD")
    
    if not db_pass:
        print("❌ SKIPPING DATA TEST: DB_PASSWORD no definido en .env")
        return

    # 1. DDL (Admin SQL) - Crear Tabla
    print(f"Probando conexión Admin SQL via Pooler a '{db_host}' (user: {db_user})...")
    
    conn = None
    max_retries = 5
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=db_host, user=db_user, password=db_pass, database="postgres",
                port=5432, connect_timeout=10
            )
            conn.autocommit = True
            print("✅ Conexión establecida.")
            break 
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️  Intento {attempt+1}/{max_retries} fallido. Reintentando en 5s...")
                time.sleep(5)
            else:
                print(f"❌ FALLO CONEXIÓN FINAL: {e}")
                print("   (Es probable que el DNS aún no se haya propagado. Espera unos minutos más).")
                return

    try:
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS tabla_prueba")
        print("Creando tabla 'tabla_prueba'...")
        cur.execute("""
            CREATE TABLE tabla_prueba (
                id SERIAL PRIMARY KEY,
                mensaje TEXT
            );
        """)
        # Deshabilitar RLS para permitir operaciones CRUD sin políticas
        cur.execute("ALTER TABLE tabla_prueba DISABLE ROW LEVEL SECURITY;")
        conn.close()
        print("✅ Tabla creada exitosamente (RLS deshabilitado).")
    except Exception as e:
        print(f"❌ FALLO DDL: {e}")
        if conn: conn.close()
        return

    # 2. CRUD (Supabase Client) - Insertar
    print("Probando Insert (Supabase Client)...")
    try:
        sb = create_client(url, keys['service_role'])
        data = {"mensaje": "Estado Inicial"}
        res = sb.table("tabla_prueba").insert(data).execute()
        print(f"✅ Insertado: {len(res.data)} filas.")
    except Exception as e:
        print(f"❌ FALLO INSERT: {e}")
        
    wait_for_user("CREACIÓN (Tabla y Datos)")

    # 3. CRUD - Editar (Update)
    print("Probando Update...")
    try:
        res = sb.table("tabla_prueba").update({"mensaje": "Estado EDITADO"}).eq("id", 1).execute()
        print(f"✅ Editado: {len(res.data)} filas.")
    except Exception as e:
        print(f"❌ FALLO UPDATE: {e}")

    wait_for_user("EDICIÓN (Datos modificados)")

    # 4. CRUD - Eliminar Fila
    print("Probando Delete Row...")
    try:
        res = sb.table("tabla_prueba").delete().eq("id", 1).execute()
        print(f"✅ Fila eliminada: {len(res.data)} filas afectadas.")
    except Exception as e:
        print(f"❌ FALLO DELETE ROW: {e}")

    wait_for_user("BORRADO DE FILA (Tabla vacía)")

    # 5. Cleanup
    print("Limpiando (DROP TABLE)...")
    try:
        conn = psycopg2.connect(
            host=db_host, user=db_user, password=db_pass, database="postgres",
            port=5432
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("DROP TABLE tabla_prueba")
        conn.close()
        print("✅ Tabla eliminada.")
    except Exception as e:
        print(f"❌ FALLO CLEANUP: {e}")


# --- MODULO 2: CREACIÓN DE PROYECTO ---
def module_create_project():
    print_step("CREACIÓN DE PROYECTO")
    manager = SupabaseManager(os.getenv("SUPABASE_ACCESS_TOKEN"))
    db_pass = os.getenv("DB_PASSWORD")
    
    if not db_pass:
         print("❌ FALTA DB_PASSWORD PARA CREAR PROYECTOS")
         return

    project_name = "prueba"
    print(f"Intentando crear proyecto: '{project_name}' en 'eu-west-1'...")
    
    try:
        # Forzar región eu-west-1 (Ireland) para mejor propagación DNS en Europa
        proj = manager.create_project(project_name, db_pass, region="eu-west-1")
        new_id = proj.get('id')
        print(f"✅ Proyecto creado exitosamente.")
        print(f"   ID: {new_id}")
        print(f"   Status Inicial: {proj.get('status')}")
        print("\n⚠️  IMPORTANTE: Ahora debes esperar unos minutos (3-5 min) para que Supabase provisione la BD y DNS.")
        print("   Cuando esté 'Active' (verde) en el Dashboard, vuelve aquí y usa la opción 2 (Pruebas de Datos).")
        
    except Exception as e:
        print(f"❌ FALLO CREACIÓN: {e}")


# --- MODULO 3: BORRADO DE PROYECTO ---
def module_delete_project():
    print_step("BORRADO DE PROYECTO")
    manager = SupabaseManager(os.getenv("SUPABASE_ACCESS_TOKEN"))
    projects = manager.list_projects()
    
    if not projects:
        print("No hay proyectos para borrar.")
        return

    print("\nTodos los Proyectos:")
    for idx, p in enumerate(projects):
        status_icon = "🟢" if p['status'] == 'ACTIVE_HEALTHY' else "🔴"
        print(f"{idx + 1}. {status_icon} {p['name']} (ID: {p['id']}, Status: {p['status']})")
    
    try:
        sel = int(input("\nSelecciona el número del proyecto a BORRAR (0 para cancelar): "))
        if sel == 0: return
        project = projects[sel - 1]
    except (ValueError, IndexError):
        print("Selección inválida.")
        return

    confirm = input(f"¿SEGURO que quieres borrar '{project['name']}' ({project['id']})? Escribe 'borrar': ")
    if confirm.lower() != 'borrar':
        print("Cancelado.")
        return

    print(f"Eliminando proyecto {project['id']}...")
    try:
        manager.delete_project(project['id'])
        print("✅ Solicitud de eliminación enviada exitosamente.")
    except Exception as e:
        if "Project not ready for deletion" in str(e):
            print("⚠️  AVISO: No se pudo borrar porque aún se está inicializando (Status != Active).")
            print("    Inténtalo de nuevo más tarde.")
        else:
            print(f"❌ Error al intentar borrar: {e}")


def main():
    while True:
        print("\n=== MENU DE DIAGNÓSTICO SUPABASE ===")
        print("1. Crear Proyecto Nuevo (Solo Crear)")
        print("2. Ejecutar Pruebas de Datos (En proyecto existente)")
        print("3. Borrar Proyecto")
        print("4. Salir")
        
        opc = input("\nSelecciona una opción: ")
        
        if opc == '1':
            module_create_project()
        elif opc == '2':
            module_test_data()
        elif opc == '3':
            module_delete_project()
        elif opc == '4':
            print("Adios.")
            break
        else:
            print("Opción no válida.")

if __name__ == "__main__":
    main()
