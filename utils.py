from pdf2image import convert_from_path
from pdf2image import convert_from_bytes
import os,stat
import shutil
from pathlib import Path
import base64
import json

import requests
from openai import OpenAI
import pandas as pd

from prompt import GPT_prompt

import subprocess


MODEL = "gpt-4o" #config['gpt_model'] # "gpt-4o"
#PDF = config['invoice_path']
#FOLDER = config['image_folder']
#api_key = config['openai_api_key']


def install_poppler_utils():
    try:
        # Exécuter la commande apt-get install pour installer poppler-utils
        subprocess.run(["apt-get", "install", "-y", "poppler-utils"], check=True)
        print("poppler-utils a été installé avec succès.")
    except subprocess.CalledProcessError as e:
        print(f"Une erreur est survenue lors de l'installation de poppler-utils : {e}")
    except Exception as e:
        print(f"Une erreur inattendue est survenue : {e}")

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
    
def pdf2img(pdf_path,folder_path):
    if os.path.isdir(folder_path):
        shutil.rmtree(folder_path)
        os.makedirs(folder_path, exist_ok=True)
    else:
        os.makedirs(folder_path, exist_ok=True)

    # Convertir le PDF en images
    images = convert_from_path(pdf_path)

    images_path = []
    for i, image in enumerate(images):
        image_path = os.path.join(folder_path, f'page_{i+1}.png')
        image.save(image_path, 'PNG')
        images_path.append(image_path)

    print(f"PDF converted to images and saved in {folder_path}")
    
    return images_path


def pdf_to_jpg(pdf_path, output_folder):
    # Creer le dossier automatique de sauvegarde
    output_folder = "/content/data"
    os.makedirs(output_folder, exist_ok=True)

    # Ouvrir le document PDF
    pdf_document = fitz.open(pdf_path)
    
    # Parcourir chaque page du document
    for page_number in range(len(pdf_document)):
        # Sélectionner la page
        page = pdf_document.load_page(page_number)
        # Extraire l'image de la page
        pix = page.get_pixmap()
        # Définir le chemin de sortie pour chaque image
        output_path = f"{output_folder}/page_{page_number + 1}.jpg"
        # Enregistrer l'image
        pix.save(output_path)
        print(f"Page {page_number + 1} enregistrée en tant que {output_path}")
        
    print("Conversion terminée")




def chat_multi_vision(image_paths, api_key, prompt):
    # Chemins des images
    base64_images = [encode_image(path) for path in image_paths]

    headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
    }

    # Construire le contenu du message de l'utilisateur avec plusieurs images
    user_content = [
        {"type": "text", "text": prompt}
    ]

    for base64_image in base64_images:
        user_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
        })
    
    #
    payload = {
    "model": MODEL,
    "messages": [
        {
            "role": "system",
            "content": "Tu es un expert en analyse de facture, qui aidera les utilisateurs à préparer des tableaux d'information précis à partir de leurs factures."
        },
        {
            "role": "user",
            "content": user_content
        }
    ],
    "temperature": 0.1,
    "top_p": 0.9,
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response



def chat_df(image_paths, api_key, prompt1):
    prompt1 = GPT_prompt()
    response1 = chat_multi_vision(image_paths, api_key, prompt1)

    table1 = response1.json()["choices"][0]['message']['content']
    
    table1json = table1.split("```json")[1].split("```")[0]
    table1json = table1.split("```json")[1].split("```")[0]

    json_str_cleaned = table1json.strip().replace('\n', '').replace('Tableau_A=', '').replace("Tableau_A =", '')
    
    
    data = json.loads(json_str_cleaned)
    df = pd.DataFrame(data)

    if "Code_Douane" not in df.columns and "Code Douane" in df.columns:
        df.rename(columns={"Code Douane": "Code_Douane"}, inplace=True)
    if "Code_Douane" not in df.columns and "CodeDouane" in df.columns:
        df.rename(columns={"CodeDouane": "Code_Douane"}, inplace=True)

    if "Valeur_Douane" not in df.columns and "Valeur Douane" in df.columns:
        df.rename(columns={"Valeur Douane": "Valeur_Douane"}, inplace=True)
    
    df['Poids_total'] = df['Poids'] * df['Quantités']

    return df



def compute_df(df_total):
    df = df_total
    
    # Création de la DataFrame pour les origines EU
    df_eu = df[df['Origine'].isin(eu_country_codes)]
    

    # Agrégation des données par code douanier pour les origines EU
    df_eu_aggregated = df_eu.groupby('Code_Douane').agg({
    'ID': lambda x: list(x),
    'Valeur': 'sum',
    'Valeur_Douane': 'sum',
    'Poids': 'sum',
    'Quantités': 'sum',
    'Poids_total': 'sum'
    }).reset_index()
    df_eu_aggregated["ORIGINE"] = "EU"

    # Renommer la colonne ID en ID_agrégés
    df_eu_aggregated.rename(columns={'ID': 'ID_agrégés'}, inplace=True)



    # Création de la DataFrame pour les origines hors EU
    df_non_eu = df[~df['Origine'].isin(eu_country_codes)]
    

    # Agrégation des données par code douanier pour les origines hors EU
    df_non_eu_aggregated = df_non_eu.groupby('Code_Douane').agg({
    'ID': lambda x: list(x),
    'Valeur': 'sum',
    'Valeur_Douane': 'sum',
    'Poids': 'sum',
    'Quantités': 'sum',
    'Poids_total': 'sum'
    }).reset_index()
    df_non_eu_aggregated["ORIGINE"] = "HORS EU"

    # Renommer la colonne ID en ID_agrégés
    df_non_eu_aggregated.rename(columns={'ID': 'ID_agrégés'}, inplace=True)


    # Concaténation des deux DataFrames
    df_combined = pd.concat([df_eu_aggregated, df_non_eu_aggregated], ignore_index=True)
    return df_combined

def EU_country(code):
    eu_country_codes = [
    "AT",  # Autriche
    "BE",  # Belgique
    "BG",  # Bulgarie
    "HR",  # Croatie
    "CY",  # Chypre
    "CZ",  # Tchéquie
    "DK",  # Danemark
    "EE",  # Estonie
    "FI",  # Finlande
    "FR",  # France
    "DE",  # Allemagne
    "GR",  # Grèce
    "HU",  # Hongrie
    "IE",  # Irlande
    "IT",  # Italie
    "LV",  # Lettonie
    "LT",  # Lituanie
    "LU",  # Luxembourg
    "MT",  # Malte
    "NL",  # Pays-Bas
    "PL",  # Pologne
    "PT",  # Portugal
    "RO",  # Roumanie
    "SK",  # Slovaquie
    "SI",  # Slovénie
    "ES",  # Espagne
    "SE",  # Suède
    "CH",  # Suisse
    ]
    if "Code" in eu_country_codes:
        return True
    else:
        return False
    

eu_country_codes = [
    "AT",  # Autriche
    "BE",  # Belgique
    "BG",  # Bulgarie
    "HR",  # Croatie
    "CY",  # Chypre
    "CZ",  # Tchéquie
    "DK",  # Danemark
    "EE",  # Estonie
    "FI",  # Finlande
    "FR",  # France
    "DE",  # Allemagne
    "GR",  # Grèce
    "HU",  # Hongrie
    "IE",  # Irlande
    "IT",  # Italie
    "LV",  # Lettonie
    "LT",  # Lituanie
    "LU",  # Luxembourg
    "MT",  # Malte
    "NL",  # Pays-Bas
    "PL",  # Pologne
    "PT",  # Portugal
    "RO",  # Roumanie
    "SK",  # Slovaquie
    "SI",  # Slovénie
    "ES",  # Espagne
    "SE",  # Suède
    "CH",  # Suisse
    ]

def convert_pdf_to_images(pdf_bytes):
    images = convert_from_bytes(pdf_bytes, fmt='jpg', dpi=300)
    return images, len(images)

# Fonction pour gérer le téléchargement et la conversion
def on_upload_change(change):
    folder_path = "./content/data"
    os.chmod(folder_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

    if os.path.isdir(folder_path):
        shutil.rmtree(folder_path)
        os.makedirs(folder_path, exist_ok=True)
    else:
        os.makedirs(folder_path, exist_ok=True)

    images, number_images = convert_pdf_to_images(change)

    images_path = []
    for i, image in enumerate(images):
        image_path = os.path.join(folder_path, f'page_{i+1}.jpg')
        image.save(image_path, 'JPEG')
        images_path.append(image_path)
    print("TEST", number_images)
