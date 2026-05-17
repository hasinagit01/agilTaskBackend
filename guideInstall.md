# Guide d'installation — Créer un projet FastAPI from scratch

Ce guide couvre toutes les étapes pour créer un projet FastAPI propre, avec SQLite, Pydantic, tests et documentation auto-générée.

---

## Prérequis

- Python 3.10 ou supérieur
- `pip` ou `pipenv` / `poetry` (au choix)

Vérifier la version Python :

```bash
python --version
```

---

## Étape 1 — Créer le dossier du projet

```bash
mkdir mon-projet-fastapi
cd mon-projet-fastapi
```

---

## Étape 2 — Créer et activer l'environnement virtuel

```bash
python -m venv .venv
```

Activation :

```bash
# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

> Le prompt du terminal affiche `(.venv)` quand l'environnement est actif.

---

## Étape 3 — Installer les dépendances

### Dépendances minimales

```bash
pip install fastapi uvicorn
```

| Package    | Rôle |
|------------|------|
| `fastapi`  | Le framework web (inclut Pydantic) |
| `uvicorn`  | Serveur ASGI pour exécuter l'app |

### Dépendances optionnelles recommandées

```bash
pip install python-dotenv   # gestion des variables d'environnement (.env)
pip install pytest httpx    # tests (httpx est le client de test de FastAPI)
```

### Geler les dépendances

```bash
pip freeze > requirements.txt
```

Pour réinstaller sur une autre machine :

```bash
pip install -r requirements.txt
```

---

## Étape 4 — Structure du projet

Structure recommandée pour un projet CRUD :

```
mon-projet-fastapi/
├── .venv/
├── api/
│   ├── __init__.py
│   └── routers/
│       ├── __init__.py
│       └── task_router.py      # routes /tasks
├── database/
│   ├── __init__.py
│   └── connection.py           # connexion SQLite
├── models/
│   ├── __init__.py
│   └── task.py                 # modèle de données interne
├── schemas/                    # équivalent des serializers — Pydantic models
│   ├── __init__.py
│   └── task_schema.py
├── services/
│   ├── __init__.py
│   └── task_service.py
├── tests/
│   ├── __init__.py
│   └── test_tasks.py
├── .env
├── main.py                     # point d'entrée de l'app FastAPI
└── requirements.txt
```

Créer les dossiers et fichiers `__init__.py` vides :

```bash
mkdir -p api/routers database models schemas services tests
touch api/__init__.py api/routers/__init__.py
touch database/__init__.py models/__init__.py schemas/__init__.py
touch services/__init__.py tests/__init__.py
```

---

## Étape 5 — Créer l'application FastAPI

### `main.py`

```python
from fastapi import FastAPI
from api.routers import task_router

app = FastAPI(
    title="Mon API CRUD",
    version="1.0.0",
)

app.include_router(task_router.router)
```

---

## Étape 6 — Créer un router

FastAPI utilise des `APIRouter` pour organiser les routes par ressource.

### `api/routers/task_router.py`

```python
from fastapi import APIRouter

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("/")
def list_tasks():
    return {"data": []}

@router.get("/{task_id}")
def get_task(task_id: int):
    return {"data": {"id": task_id}}
```

> `prefix="/tasks"` évite de répéter `/tasks` dans chaque route.
> `tags=["tasks"]` regroupe les routes dans Swagger.

---

## Étape 7 — Créer des schemas Pydantic

Les schemas Pydantic remplacent les serializers et les validators manuels.
FastAPI les utilise pour **valider les entrées** et **sérialiser les sorties** automatiquement.

### `schemas/task_schema.py`

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class TaskCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = None

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

> `model_config = {"from_attributes": True}` permet de construire le schema depuis un objet Python (utile avec un ORM ou un `dataclass`).

Utilisation dans un router :

```python
from schemas.task_schema import TaskCreate, TaskResponse

@router.post("/", response_model=TaskResponse, status_code=201)
def create_task(body: TaskCreate):
    # FastAPI valide automatiquement le body et renvoie une 422 si invalide
    ...
```

---

## Étape 8 — Lancer l'application

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

| Option     | Rôle |
|------------|------|
| `main:app` | fichier `main.py`, variable `app` |
| `--reload` | rechargement automatique à chaque modification (dev uniquement) |
| `--host`   | interface d'écoute |
| `--port`   | port |

---

## Étape 9 — Documentation automatique

FastAPI génère deux interfaces de documentation sans aucune configuration :

| URL | Interface |
|-----|-----------|
| `http://localhost:8000/docs` | Swagger UI (interactive) |
| `http://localhost:8000/redoc` | ReDoc (lecture) |
| `http://localhost:8000/openapi.json` | Spec OpenAPI brute |

> Aucun code supplémentaire n'est nécessaire. La doc est générée à partir des schemas Pydantic et des annotations de type.

---

## Étape 10 — Variables d'environnement

### `.env`

```env
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./database.db
```

### `config.py`

```python
from dotenv import load_dotenv
import os

load_dotenv()

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")
```

---

## Étape 11 — Gestion des erreurs

FastAPI expose `HTTPException` pour retourner des erreurs HTTP propres :

```python
from fastapi import HTTPException

@router.get("/{task_id}")
def get_task(task_id: int):
    task = service.find_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Tâche {task_id} non trouvée")
    return {"data": task}
```

Pour un handler global (ex. BusinessError maison) :

```python
from fastapi import Request
from fastapi.responses import JSONResponse
from services.business_error import BusinessError

@app.exception_handler(BusinessError)
async def business_error_handler(request: Request, exc: BusinessError):
    return JSONResponse(status_code=422, content={"error": str(exc)})
```

---

## Étape 12 — Tests

FastAPI fournit un `TestClient` basé sur `httpx`.

### `tests/test_tasks.py`

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_list_tasks():
    response = client.get("/tasks/")
    assert response.status_code == 200

def test_create_task():
    response = client.post("/tasks/", json={"title": "Test", "description": "desc"})
    assert response.status_code == 201
```

Lancer les tests :

```bash
pytest
pytest -v          # mode verbose
pytest tests/      # cibler un dossier
```

---

## Récapitulatif des commandes clés

```bash
# Créer et activer l'env virtuel
python -m venv .venv && source .venv/bin/activate

# Installer les dépendances
pip install fastapi uvicorn python-dotenv pytest httpx

# Lancer le serveur (dev)
uvicorn main:app --reload --port 8000

# Lancer les tests
pytest -v

# Geler les dépendances
pip freeze > requirements.txt
```

---

## Différences clés avec `http.server` (Python stdlib)

| Fonctionnalité | `http.server` (stdlib) | FastAPI |
|---|---|---|
| Router | Manuel (`Router` custom) | `APIRouter` natif |
| Validation des entrées | Validators manuels | Pydantic automatique |
| Serialization | Serializers manuels | Pydantic automatique |
| Documentation | `openapi.py` manuel | Générée automatiquement |
| Gestion des erreurs | Try/except dans `_dispatch` | `HTTPException` + handlers |
| CORS | Headers manuels | Middleware `CORSMiddleware` |
| Tests | `pytest` + requêtes manuelles | `TestClient` intégré |
| Performances | Synchrone (WSGI-like) | Asynchrone (ASGI) |
