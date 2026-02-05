"""
==============================================
AgenteSupabaseAI - Test de Conexión
==============================================
Script de diagnóstico para probar diferentes métodos de conexión:
1. Conexión directa (IPv6) - Probablemente fallará si no tienes IPv6
2. Session Pooler (puerto 5432) - Recomendado para aplicaciones
3. Transaction Pooler (puerto 6543) - Para conexiones de corta duración

Uso:
    python diagnostico/test_connection.py

IMPORTANTE: Configura el project_ref y asegúrate de tener
SUPABASE_POOLER_HOST en tu .env si falla la conexión directa.

Autor: JoseLuisLopezArrocha
Licencia: MIT
==============================================
"""

import os
import sys
import psycopg2

# Configurar path para imports
sys.path.append('.')
from dotenv import load_dotenv

load_dotenv()

# ==============================================
# CONFIGURACIÓN DEL PROYECTO A PROBAR
# ==============================================
# Cambia esto al ID de tu proyecto (lo ves en el dashboard de Supabase)
project_ref = "mkejdhjxwhjikwcartdu"
db_pass = os.getenv("DB_PASSWORD")

print(f"DB_PASSWORD: {'SET' if db_pass else 'NOT SET'}")
print(f"Password length: {len(db_pass) if db_pass else 0}")

# Prueba 1: Conexión directa (IPv6 - probablemente fallará)
print("\n--- PRUEBA 1: Conexión directa (db.*.supabase.co) ---")
try:
    conn = psycopg2.connect(
        host=f"db.{project_ref}.supabase.co",
        user="postgres",
        password=db_pass,
        database="postgres",
        port=5432,
        connect_timeout=5
    )
    print("✅ Conexión directa exitosa")
    conn.close()
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")

# Prueba 2: Pooler puerto 5432 (Session Mode)
print("\n--- PRUEBA 2: Pooler Session (puerto 5432) ---")
try:
    conn = psycopg2.connect(
        host="aws-1-eu-west-1.pooler.supabase.com",
        user=f"postgres.{project_ref}",
        password=db_pass,
        database="postgres",
        port=5432,
        connect_timeout=10
    )
    print("✅ Pooler Session exitoso")
    conn.close()
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")

# Prueba 3: Pooler puerto 6543 (Transaction Mode)
print("\n--- PRUEBA 3: Pooler Transaction (puerto 6543) ---")
try:
    conn = psycopg2.connect(
        host="aws-1-eu-west-1.pooler.supabase.com",
        user=f"postgres.{project_ref}",
        password=db_pass,
        database="postgres",
        port=6543,
        connect_timeout=10
    )
    print("✅ Pooler Transaction exitoso")
    conn.close()
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")

print("\n--- Fin de pruebas ---")
