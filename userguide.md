# Contexte du projet

Cette application est un simple CRUD utilisant une base de données SQLite.

## Structure du projet

Le projet contient les dossiers suivants :

- `database`
  - contient la connexion SQLite
  - les migrations
  - les repositories

- `models`
  - contient les modèles de données

- `services`
  - contient la logique métier

- `ui`
  - contient les commandes et l'interface utilisateur console

- `api`
  - `handler.py` : handler HTTP générique, dispatche les requêtes via le router
  - `router.py` : registre des routes `(méthode, pattern, handler)`
  - `openapi.py` : spec OpenAPI 3.0 (schemas + endpoints)
  - `controllers/task_controller.py` : routes `/tasks` + appels `TaskService`
  - `controllers/docs_controller.py` : routes `/docs` et `/openapi.json`

- `serializers`
  - `base_serializer.py` : `BaseSerializer` avec enveloppe `{"data": ...}`
  - `task_serializer.py` : `TaskSerializer` pour le modèle `Task`

- `validators`
  - contient les validateurs de données

- `utils`
  - contient les utilitaires (mapper, etc.)

Autres fichiers :
- `database.db` : base de données SQLite
- `main.py` : point d'entrée de l'application console
- `server.py` : point d'entrée de l'API REST
- `seed.py` : script de peuplement de la base avec 30 tâches de test

---

## Peupler la base de données (seed)

Pour insérer 30 tâches de test en une seule commande :

```bash
python seed.py
```

Sortie attendue :
```
  [01] Configurer l'environnement de développement
  [02] Créer la structure du projet
  ...
  [30] Préparer le déploiement

30/30 tâches insérées.
```

> Le script passe par `TaskService` — la validation métier s'applique normalement.
> Les doublons sont ignorés (`[SKIP]`) si le script est relancé plusieurs fois.

Utile pour tester la pagination :
```bash
python server.py
curl "http://localhost:8000/tasks?page=1&limit=5"   # page 1 sur 6
curl "http://localhost:8000/tasks?page=3&limit=10"  # page 3 sur 3
```

---

## Lancer l'application console

```bash
python main.py
```

---

## Lancer l'API REST

```bash
python server.py
```

Le serveur démarre sur `http://localhost:8000` et affiche les routes disponibles :

```
API démarrée sur http://localhost:8000
  GET      ^/tasks/?$
  POST     ^/tasks/?$
  GET      ^/tasks/(\d+)/?$
  PUT      ^/tasks/(\d+)/?$
  DELETE   ^/tasks/(\d+)/?$
  GET      ^/docs/?$
  GET      ^/openapi\.json$
```

Pour arrêter le serveur : `Ctrl+C`

---

## Swagger UI

L'interface Swagger est disponible sans installation supplémentaire (chargée via CDN).

**Accès :** ouvrir [http://localhost:8000/docs](http://localhost:8000/docs) dans le navigateur après avoir lancé le serveur.

La spec OpenAPI brute est accessible sur :

```bash
curl http://localhost:8000/openapi.json
```

---

## Format des réponses

Toutes les réponses sont enveloppées dans une clé `data` :

```json
// Réponse single
{ "data": { "id": 1, "title": "Ma tâche", ... } }

// Réponse collection
{ "data": [ { "id": 1, ... }, { "id": 2, ... } ] }

// Réponse erreur (pas d'enveloppe data)
{ "error": "Message d'erreur" }
```

---

## Endpoints

### Lister toutes les tâches

Supporte la pagination via les query params `page` et `limit`.

| Paramètre | Type | Défaut | Contrainte |
|-----------|------|--------|------------|
| `page`    | int  | `1`    | >= 1       |
| `limit`   | int  | `10`   | 1 – 100    |

```bash
# Défaut (page 1, 10 résultats)
curl http://localhost:8000/tasks

# Page 2 avec 3 résultats par page
curl "http://localhost:8000/tasks?page=2&limit=3"
```

Réponse `200` :
```json
{
  "data": [
    {
      "id": 1,
      "title": "Ma tâche",
      "description": "Description",
      "created_at": "2025-12-04T14:48:09",
      "updated_at": "2025-12-04T14:48:09"
    }
  ],
  "meta": {
    "current_page": 1,
    "per_page": 10,
    "total": 125,
    "last_page": 13,
    "from": 1,
    "to": 10,
    "has_next_page": true,
    "has_previous_page": false
  }
}
```

Réponse `400` si les paramètres sont invalides :
```json
{ "error": "Les paramètres page et limit doivent être des entiers" }
```

---

### Récupérer une tâche par ID

```bash
curl http://localhost:8000/tasks/1
```

Réponse `200` :
```json
{
  "data": {
    "id": 1,
    "title": "Ma tâche",
    "description": "Description",
    "created_at": "2025-12-04T14:48:09",
    "updated_at": "2025-12-04T14:48:09"
  }
}
```

Réponse `404` si non trouvée :
```json
{ "error": "Tâche 1 non trouvée" }
```

---

### Créer une tâche

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Nouvelle tâche", "description": "Ma description"}'
```

Réponse `201` :
```json
{
  "data": {
    "id": 14,
    "title": "Nouvelle tâche",
    "description": "Ma description",
    "created_at": "2026-05-15T07:44:29",
    "updated_at": "2026-05-15T07:44:29"
  }
}
```

Réponse `422` si le titre est invalide :
```json
{ "error": "Le titre doit contenir au moins 2 caractères" }
```

---

### Mettre à jour une tâche

```bash
curl -X PUT http://localhost:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"title": "Titre modifié", "description": "Description modifiée"}'
```

Réponse `200` :
```json
{
  "data": {
    "id": 1,
    "title": "Titre modifié",
    "description": "Description modifiée",
    "created_at": "2025-12-04T14:48:09",
    "updated_at": "2026-05-15T07:44:29"
  }
}
```

Réponse `404` si la tâche n'existe pas :
```json
{ "error": "Tâche ID 1 non trouvée" }
```

---

### Supprimer une ou plusieurs tâches

Accepte une liste d'IDs. Fonctionne pour un seul ID comme pour plusieurs.
Les IDs inexistants sont ignorés — la réponse indique combien ont réellement été supprimés.

```bash
# Supprimer une seule tâche
curl -X DELETE http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"ids": [1]}'

# Supprimer plusieurs tâches
curl -X DELETE http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"ids": [1, 2, 3]}'
```

Réponse `200` :
```json
{
  "data": {
    "requested": 3,
    "deleted": 2
  }
}
```

> `requested` = nombre d'IDs envoyés, `deleted` = nombre réellement supprimés en base.

Réponse `422` si la liste est vide :
```json
{ "error": "La liste d'IDs est vide" }
```

Réponse `400` si le format est invalide :
```json
{ "error": "Tous les IDs doivent être des entiers" }
```

---

## Codes HTTP

| Code | Signification |
|------|---------------|
| `200` | Succès |
| `201` | Ressource créée |
| `400` | Corps de requête manquant ou JSON invalide |
| `404` | Route ou ressource non trouvée |
| `422` | Erreur de validation métier |
