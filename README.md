# 🚴 Tour de France 2026 — Calendrier iCal

Flux iCal avec les 21 étapes du TDF 2026, hébergé sur GitHub Pages.

## Structure

```
ical_tdf_2026/
├── stages.json                  # Données des étapes (éditer ici)
├── generate.py                  # Génère public/tdf2026.ics
├── public/
│   ├── index.html               # Page d'accueil avec boutons télécharger / s'abonner
│   └── tdf2026.ics              # Fichier généré (ne pas éditer à la main)
└── .github/workflows/
    └── deploy.yml               # GitHub Action : génère + déploie sur Pages
```

## Setup initial

```bash
# 1. Créer le repo sur GitHub
gh repo create ical_tdf_2026 --public --source=. --push

# 2. Activer GitHub Pages
#    → Settings → Pages → Source : GitHub Actions

# 3. Premier déploiement
git add -A && git commit -m "init" && git push
```

L'Action génère le `.ics` et le déploie automatiquement.

URL du calendrier : `https://antoberg.github.io/ical_tdf_2026/tdf2026.ics`

## Mettre à jour les données

1. Modifier `stages.json` (ajouter résultats, corriger infos…)
2. `git add stages.json && git commit -m "update étape X" && git push`
3. L'Action régénère et redéploie en ~30 secondes

## Tester en local

```bash
python3 generate.py
# → public/tdf2026.ics généré
```

## Contenu de chaque événement

| Champ iCal    | Contenu                                    |
|---------------|--------------------------------------------|
| `SUMMARY`     | Emoji + n° + villes + km                   |
| `LOCATION`    | Ville d'arrivée (géolocalisable)           |
| `DESCRIPTION` | Type, D+, cols détaillés, texte, favoris   |
| `URL`         | Lien vers le profil sur letour.fr          |
| `VALARM`      | Rappel le matin de l'étape (8h)            |
