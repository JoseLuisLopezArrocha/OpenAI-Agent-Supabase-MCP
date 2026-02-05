# 🚀 Cómo subir tu proyecto a GitHub

Como no tienes configurado `git` ni `gh` CLI, hemos preparado los archivos pero necesitas ejecutar estos comandos finales manualmente.

## 1. Configura tu Identidad (Solo si es tu primera vez)
Abre una terminal en la carpeta del proyecto y ejecuta:
```powershell
git config --global user.name "Tu Nombre"
git config --global user.email "tu@email.com"
```

## 2. Guarda los cambios (Commit)
Hemos inicializado el repositorio, ahora confirma los archivos:
```powershell
git commit -m "Initial commit: OpenAI Agent + Supabase + MCP"
```

## 3. Crea el Repositorio en GitHub
1. Ve a [github.com/new](https://github.com/new)
2. Nombre del repositorio: `AgenteSupabaseAI` (o el que gustes)
3. **NO** marques "Initialize with README" (ya tenemos uno).
4. Dale a "Create repository".

## 4. Conecta y Sube
Copia los comandos que te da GitHub bajo "…or push an existing repository from the command line" y ejecútalos. Se verán así:

```powershell
git remote add origin https://github.com/TU-USUARIO/AgenteSupabaseAI.git
git branch -M main
git push -u origin main
```

¡Listo! Tu proyecto estará online.
