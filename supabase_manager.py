"""
==============================================
AgenteSupabaseAI - Gestor de la API de Supabase
==============================================
Clase auxiliar para interactuar con la Management API de Supabase.
Permite listar proyectos, obtener API keys, crear y eliminar proyectos.

Documentación API:
    https://supabase.com/docs/reference/api/introduction

Autor: JoseLuisLopezArrocha
Licencia: MIT
==============================================
"""

import requests
from typing import List, Dict, Optional
import time

class SupabaseManager:
    """
    Gestiona la interacción con la API de Gestión de Supabase (Management API).
    Permite listar proyectos, obtener llaves y crear nuevos proyectos.
    """
    
    API_URL = "https://api.supabase.com/v1"

    def __init__(self, access_token: str):
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    def _get(self, endpoint: str) -> Dict:
        response = requests.get(f"{self.API_URL}/{endpoint}", headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Error GET {endpoint}: {response.text}")
        return response.json()

    def _post(self, endpoint: str, data: Dict) -> Dict:
        response = requests.post(f"{self.API_URL}/{endpoint}", json=data, headers=self.headers)
        if response.status_code not in [200, 201]:
            raise Exception(f"Error POST {endpoint}: {response.text}")
        return response.json()

    def list_projects(self) -> List[Dict]:
        """Devuelve una lista de todos los proyectos en la cuenta."""
        return self._get("projects")

    def get_project_api_keys(self, project_ref: str) -> Dict[str, str]:
        """
        Obtiene las API KEYS (anon, service_role) de un proyecto específico.
        """
        keys_data = self._get(f"projects/{project_ref}/api-keys")
        
        # Mapear a un formato más simple
        result = {}
        for k in keys_data:
            result[k['name']] = k['api_key']
        return result

    def get_organizations(self) -> List[Dict]:
        """Lista las organizaciones para saber dónde crear el proyecto."""
        return self._get("organizations")

    def create_project(self, name: str, db_pass: str, organization_id: str = None, region: str = "eu-west-1") -> Dict:
        """
        Crea un nuevo proyecto en Supabase.
        Si no se da organization_id, usa la primera disponible.
        """
        if not organization_id:
            orgs = self.get_organizations()
            if not orgs:
                raise Exception("No se encontraron organizaciones en esta cuenta.")
            organization_id = orgs[0]['id']
            print(f"[SupabaseManager] Usando organización por defecto: {orgs[0]['name']}")

        payload = {
            "name": name,
            "organization_id": organization_id,
            "db_pass": db_pass,
            "region": region,
            "plan": "free" # Intentar usar free tier
        }

        print(f"[SupabaseManager] Enviando solicitud de creación para '{name}'...")
        project = self._post("projects", payload)
        
        # Esperar a que el proyecto esté listo (Opcional, puede tardar minutos)
        # Por ahora devolvemos el objeto proyecto inmediatamente.
        return project

    def delete_project(self, project_ref: str) -> Dict:
        """
        Elimina un proyecto existente.
        ADVERTENCIA: Acción destructiva irreversible.
        """
        print(f"[SupabaseManager] Eliminando proyecto '{project_ref}'...")
        response = requests.delete(f"{self.API_URL}/projects/{project_ref}", headers=self.headers)
        if response.status_code != 200:
             # A veces devuelve 204 o 200 con el objeto borrado
             # Si falla (ej 404, 403) lanzamos excepcion
             raise Exception(f"Error DELETE project {project_ref}: {response.text}")
        return response.json()
