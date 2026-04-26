DESCRIPTION = """
## Supply Chain Demand Forecasting API

Ce backend prédit les ruptures de stock et recommande les meilleurs fournisseurs.

### Flux typique

1. **`POST /forecasting/predict`** — Prédire la demande pour un article/magasin
2. **`POST /recommendations/suppliers`** — Obtenir les fournisseurs classés selon la prévision
3. **`POST /orders/drafts`** — Créer un bon de commande en brouillon
4. **`POST /orders/{id}/confirm`** — Confirmer et soumettre la commande à AP2

### Données disponibles

Le modèle Chronos est entraîné sur des données historiques couvrant :
- **Magasins** : 1 à 10
- **Articles** : 1 à 50
- **Période** : 2013-01-01 → 2017-12-31
- **Ventes moyennes** : ~52 unités/jour (max 231)
"""

TAGS_METADATA = [
    {
        "name": "forecasting",
        "description": "Prévision de la demande via Amazon Chronos T5.",
    },
    {
        "name": "recommendations",
        "description": "Classement des fournisseurs basé sur la prévision Chronos.",
    },
    {
        "name": "suppliers",
        "description": "Gestion du référentiel fournisseurs.",
    },
    {
        "name": "inventory",
        "description": "Snapshots du niveau de stock actuel.",
    },
    {
        "name": "orders",
        "description": "Création et confirmation des bons de commande (intégration AP2).",
    },
    {
        "name": "health",
        "description": "Liveness check.",
    },
]
