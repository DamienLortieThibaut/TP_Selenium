# Doctolib Web Scraper

Ce projet est un script Python utilisant Selenium pour extraire des informations sur les médecins disponibles sur Doctolib. Il permet de filtrer les résultats en fonction de plusieurs critères et d'exporter les données dans un fichier CSV.

## Fonctionnalités

- Recherche de médecins sur Doctolib en fonction de critères spécifiques.
- Filtrage des résultats par :
  - Type de consultation (présentiel, vidéoconférence ou les deux).
  - Type d'assurance.
  - Disponibilités dans une plage de dates.
  - Localisation.
- Export des résultats dans un fichier CSV.

## Prérequis

- Python 3.10 ou supérieur.
- Navigateur Firefox.
- Geckodriver (pour Selenium).
- Les bibliothèques Python suivantes :
  - `selenium`
  - `argparse`
  - `csv`

## Installation

1. Clonez ce dépôt ou téléchargez les fichiers.
2. Installez les dépendances nécessaires avec la commande suivante :
   ```bash
   pip install selenium
   ```
3. Assurez-vous que Geckodriver est installé et accessible dans votre `PATH`.

## Utilisation

Exécutez le script avec les arguments suivants :

```bash
python doctolib_scheduled.py --max-results <nombre> --start-date <JJ/MM/AAAA> --end-date <JJ/MM/AAAA> --query <spécialité> --insurance <type assurance> --address-keyword <localisation> --video-conference <yes|no|both>
```

### Arguments

- `--max-results` : Nombre maximum de résultats à collecter (par défaut : 10).
- `--start-date` : Date de début pour les disponibilités (format `JJ/MM/AAAA`).
- `--end-date` : Date de fin pour les disponibilités (format `JJ/MM/AAAA`).
- `--query` : Spécialité médicale (exemple : "Médecin généraliste").
- `--insurance` : Type d'assurance (exemple : "Conventionné secteur 1").
- `--address-keyword` : Localisation (exemple : "Paris").
- `--video-conference` : Filtrer par type de consultation :
  - `yes` : Uniquement les vidéoconférences.
  - `no` : Uniquement les consultations en présentiel.
  - `both` : Les deux (par défaut).

### Exemple

```bash
python doctolib_scheduled.py --max-results 15 --start-date 01/05/2025 --end-date 31/05/2025 --query "Médecin généraliste" --insurance "Conventionné secteur 1" --address-keyword "Paris" --video-conference "both"
```

## Résultats

Les résultats sont exportés dans un fichier CSV nommé `doctors_data.csv`. Ce fichier contient les colonnes suivantes :

- Vidéoconférence (Oui/Non)
- Nom
- Adresse
- Code Postal
- Ville
- Secteur Assurance
- Disponibilités

## Limitations

- Le script dépend de la structure HTML de Doctolib. Toute modification de cette structure peut casser le script.
- Le script est conçu pour fonctionner avec Firefox et Geckodriver.

## Axe d'amelioration

- Meilleur utilisation des WebDriverWait car avec l'utilisation que j'en faisais, cela me creer des conflits
- Ajouter la gestion de recuperation du prix de la consultation

## Avertissement

Ce projet est uniquement à des fins éducatives. Assurez-vous de respecter les conditions d'utilisation de Doctolib et les lois locales concernant le scraping de données.