from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, ElementClickInterceptedException
from datetime import datetime
import time
import csv
import argparse
import unicodedata

# Dictionnaire des mois
MONTHS = {
    "janvier": "01",
    "février": "02",
    "mars": "03",
    "avril": "04",
    "mai": "05",
    "juin": "06",
    "juillet": "07",
    "août": "08",
    "septembre": "09",
    "octobre": "10",
    "novembre": "11",
    "décembre": "12"
}

# Fonction pour convertir les dates en objets datetime
def parse_availability_date_custom(date_str):
    try:
        parts = date_str.split()
        current_year = datetime.now().year
        current_month = datetime.now().month

        # Format court : "ven. 9 mai 10:45"
        if len(parts) == 4:
            day, month, time = parts[1], parts[2], parts[3]
            month_number = MONTHS.get(month.lower())
            if not month_number:
                raise ValueError(f"Mois inconnu : {month}")
            
            # Gérer le cas de la nouvelle année
            if int(month_number) < current_month:
                year = current_year + 1
            else:
                year = current_year
            
            return datetime.strptime(f"{day} {month_number} {year} {time}", "%d %m %Y %H:%M")
        
        # Format long : "12 mai 2025"
        elif len(parts) == 3:
            day, month, year = parts[0], parts[1], parts[2]
            month_number = MONTHS.get(month.lower())
            if not month_number:
                raise ValueError(f"Mois inconnu : {month}")
            return datetime.strptime(f"{day} {month_number} {year}", "%d %m %Y")
        else:
            raise ValueError(f"Format inattendu pour la chaîne : {date_str}")
    except ValueError as e:
        print(f"Erreur de format de date pour la chaîne : {date_str} - {e}")
        return None

# Simuler un défilement jusqu'au bas de la page
def scroll_to_bottom(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

# Ajouter argparse pour les filtres
def parse_arguments():
    parser = argparse.ArgumentParser(description="Filtrer les résultats des médecins sur Doctolib.")
    parser.add_argument("--max-results", type=int, default=10, help="Nombre maximum de résultats à afficher.")
    parser.add_argument("--start-date", type=str, help="Date de début pour les disponibilités (format JJ/MM/AAAA).")
    parser.add_argument("--end-date", type=str, help="Date de fin pour les disponibilités (format JJ/MM/AAAA).")
    parser.add_argument("--query", type=str, help="Requête médicale (ex : 'dermatologue', 'généraliste').")
    parser.add_argument("--insurance", type=str, help="Type d'assurance.")
    parser.add_argument("--address-keyword", type=str, help="Mot-clé pour filtrer les adresses.")
    parser.add_argument("--video-conference", type=str, choices=["yes", "no", "both"], default="both", 
                        help="Filtrer sur les videoconférences : 'yes' pour uniquement les vidéoconférences, 'no' pour uniquement les présentiels, 'both' pour les deux (par défaut).")
    return parser.parse_args()

# Fonction pour vérifier si une date est dans une plage donnée
def is_within_date_range(date, start_date, end_date):
    if start_date and date < start_date:
        return False
    if end_date and date > end_date:
        return False
    return True

# Fonction pour exporter les données dans un fichier CSV
def export_to_csv(doctors_data, filename="doctors_data.csv"):
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow(["Vidéoconférence", "Nom", "Adresse", "Code Postal", "Ville", "Secteur Assurance", "Disponibilités"])
        
        for doctor in doctors_data:
            writer.writerow([
                "Oui" if doctor["video_conference"] else "Non",
                doctor["name"],
                doctor["street"],
                doctor["postal_code"],
                doctor["city"],
                doctor["insurance_sector"],
                ", ".join([availability.strftime("%d/%m/%Y %H:%M") for availability in doctor["availabilities"]])
            ])

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

# Fonction principale
if __name__ == "__main__":
    args = parse_arguments()

    start_date = datetime.strptime(args.start_date, "%d/%m/%Y") if args.start_date else None
    end_date = datetime.strptime(args.end_date, "%d/%m/%Y") if args.end_date else None

    driver = webdriver.Firefox()
    driver.get("https://www.doctolib.fr/")

    wait = WebDriverWait(driver, 10)

    try:
        consent_button = wait.until(
            EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
        )
        consent_button.click()
    except Exception as e:
        print("Pas de popup Didomi détecté ou déjà fermé.")

    base_url = "https://www.doctolib.fr"
    query = remove_accents(args.query.replace(" ", "-").lower()) if args.query else "medecin-generaliste"
    address_keyword = remove_accents(args.address_keyword.replace(" ", "-").lower()) if args.address_keyword else "paris"
    specific_url = f"{base_url}/{query}/{address_keyword}"

    # Naviguer directement vers l'URL spécifique pour eviter le rootage random entre https://www.doctolib.fr/medecin-generaliste/paris et https://www.doctolib.fr/search?location=paris&speciality=medecin-generaliste
    driver.get(specific_url)
    time.sleep(5)

    doctors_data = []
    while len(doctors_data) < args.max_results:
        print(f"Nombre actuel de médecins collectés : {len(doctors_data)}")
        scroll_to_bottom(driver)
        time.sleep(2)

        # Récupérer les médecins sur la page actuelle
        list_doctor = driver.find_elements(By.CSS_SELECTOR, "ul.list-none.flex.flex-col.gap-16.p-8.w-full li.w-full")
        print(f"Nombre de médecins trouvés sur cette page : {len(list_doctor)}")

        if not list_doctor:
            print("Aucun médecin trouvé sur cette page. Fin de la collecte.")
            break

        for doctor in list_doctor:
            article = doctor.find_element(By.CSS_SELECTOR, "article.dl-card.dl-card-bg-white.dl-card-variant-default.search-result-card.dl-padding-16.scroll-mt-\\[70px\\]")
            
            name_div = article.find_element(By.CSS_SELECTOR, "div.dl-flex-row.dl-flex-grow")
            name_h2 = name_div.find_element(By.CSS_SELECTOR, "h2.dl-text.dl-text-body.dl-text-bold.dl-text-s.dl-text-primary-110")
            full_name = name_h2.text.split("Dr")[-1].strip()

            try:
                video_conference = article.find_element(By.CSS_SELECTOR, "div.dl-round-icon-placeholder.dl-flex-center.dl-position-absolute")
                video_conference_available = True
            except NoSuchElementException:
                video_conference_available = False
            
            if args.video_conference == "yes" and not video_conference_available:
                continue
            if args.video_conference == "no" and video_conference_available:
                continue
            
            address_div = article.find_element(By.CSS_SELECTOR, "div.mt-8 > div.mt-8.gap-8.flex")
            address_info = address_div.find_element(By.CSS_SELECTOR, "div.flex.flex-wrap.gap-x-4")
            street = address_info.find_elements(By.CSS_SELECTOR, "p.dl-text.dl-text-body.dl-text-regular.dl-text-s.dl-text-neutral-130")[0].text
            postal_city = address_info.find_elements(By.CSS_SELECTOR, "p.dl-text.dl-text-body.dl-text-regular.dl-text-s.dl-text-neutral-130")[1].text
            postal_code = postal_city[:5]
            city = postal_city[6:].strip()
                    
            insurance_divs = article.find_elements(By.CSS_SELECTOR, "div.mt-8.gap-8.flex")
            if len(insurance_divs) > 1:
                insurance_sector = insurance_divs[1].find_element(By.CSS_SELECTOR, "p.dl-text.dl-text-body.dl-text-regular.dl-text-s.dl-text-neutral-130").text
            else:
                insurance_sector = "N/A"
            
            if args.insurance and args.insurance.lower() not in insurance_sector.lower():
                continue
            
            availabilities_data = []
            try:
                article = doctor.find_element(By.CSS_SELECTOR, "article.dl-card.dl-card-bg-white.dl-card-variant-default.dl-card-border.dl-padding-0.dl-p-doctor-result-card")
                
                # Vérifier la présence de la div enfant avec la classe spécifiée
                tappable_div = article.find_elements(By.CSS_SELECTOR, "div.Tappable-inactive.dl-card.dl-card-bg-white.dl-card-variant-default.dl-card-tappable")
                if tappable_div:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tappable_div[0])
                    time.sleep(1)
                    tappable_div[0].click()
                    time.sleep(1)
                
                availabilities_container = article.find_element(By.CSS_SELECTOR, "div.md\\:col-span-5.p-16")
                availability_days = availabilities_container.find_elements(By.CSS_SELECTOR, "div.dl-desktop-availabilities.dl-desktop-availabilities-flat")
                
                for day in availability_days:
                    try:
                        see_more_button = day.find_element(By.CSS_SELECTOR, "button.dl-button.dl-button-tertiary-primary.dl-button-size-medium")
                        time.sleep(1)
                        see_more_button.click()
                        time.sleep(2)
                    except NoSuchElementException:
                        print("Bouton 'Voir plus d'horaires' non trouvé sur cette page.")
                        pass
                    except ElementNotInteractableException as e:
                        print(f"Erreur : {e}. Le bouton 'Voir plus d'horaires' n'est pas interactif.")
                        pass

                    slots = day.find_elements(By.CSS_SELECTOR, "div.Tappable-inactive.availabilities-slot.availabilities-slot-desktop")
                    for slot in slots:
                        if slot.get_attribute("aria-label"):
                            availabilities_data.append(slot.get_attribute("aria-label"))
                    
            except NoSuchElementException:
                availabilities_data = ["N/A"]
            availabilities_data = [parse_availability_date_custom(date_str) for date_str in availabilities_data if parse_availability_date_custom(date_str) is not None]
            
            # Filtrer par période de disponibilité
            availabilities_data = [
                availability for availability in availabilities_data
                if is_within_date_range(availability, start_date, end_date)
            ]

            doctors_data.append({
                "video_conference": video_conference_available,
                "name": full_name,
                "street": street,
                "postal_code": postal_code,
                "city": city,
                "insurance_sector": insurance_sector,
                "availabilities": availabilities_data
            })

            if len(doctors_data) >= args.max_results:
                break

        try:
            next_button = driver.find_element(By.CSS_SELECTOR, "button.next-link, a.Tappable-inactive.dl-button-tertiary-primary.p-0.dl-button.dl-button-size-medium")
            driver.execute_script("arguments[0].scrollIntoView({block: 'nearest'});", next_button)
            
            if next_button.is_displayed() and next_button.is_enabled():
                print("Clic sur le bouton 'Suivant' pour charger la page suivante...")
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(5)
                scroll_to_bottom(driver)  
                time.sleep(2)
            else:
                print("Le bouton 'Suivant' n'est pas visible ou activé.")
                break
        except NoSuchElementException:
            print("Bouton 'Suivant' non trouvé, fin de la pagination.")
            break

    export_to_csv(doctors_data)
    print(f"Les résultats ont été exportés dans le fichier 'doctors_data.csv'.")
    print("Nombre total de médecins collectés : ", len(doctors_data))