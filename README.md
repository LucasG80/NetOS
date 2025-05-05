# NetOS - Utilitaire de maintenance système

## Description

NetOS est un outil de maintenance système avancé, développé en Python, qui offre plusieurs fonctionnalités pour optimiser et réparer votre système Windows.

## Fonctionnalités principales

- **Nettoyage des fichiers temporaires** : Supprime les fichiers temporaires pour libérer de l'espace disque
- **Création de points de restauration** : Crée des points de restauration système avant d'effectuer des modifications importantes
- **Réparation système** : Utilise SFC et DISM pour réparer les fichiers système corrompus
- **Nettoyage de disque** : Lance l'utilitaire de nettoyage de disque Windows avec des paramètres optimisés

## Prérequis

- Windows 10 ou supérieur
- Python 3.6 ou supérieur
- Privilèges administrateur (l'application demande automatiquement l'élévation)

## Installation

1. Clonez ce dépôt ou téléchargez les fichiers sources
2. Assurez-vous que Python est installé sur votre système

## Utilisation

Lancez l'application en exécutant :

```bash
python NetOs.py
```

L'interface graphique vous permettra de:

1. Sélectionner les actions à effectuer
2. Lancer les opérations via le bouton "Lancer les actions sélectionnées"
3. Suivre la progression des opérations dans le journal d'activité

## Journalisation

Toutes les opérations sont enregistrées dans un fichier journal situé dans le dossier `logs`. Ce fichier peut être utile pour diagnostiquer d'éventuels problèmes.

## Sécurité

NetOS crée automatiquement un point de restauration (si cette option est sélectionnée) avant d'effectuer des modifications importantes sur le système, garantissant ainsi la possibilité de revenir à un état fonctionnel en cas de problème.

## Contributeurs

- [lighscent](https://github.com/lighscent)

## Licence

Ce projet est distribué sous licence MIT. Consultez le fichier `LICENSE` pour plus de détails.
