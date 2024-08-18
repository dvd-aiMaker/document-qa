from pdf2image import convert_from_path
from pdf2image import convert_from_bytes
import os, stat, re
import shutil
from pathlib import Path
import base64
import json
import fitz

import requests
from openai import OpenAI
import pandas as pd

from prompt import GPT_prompt
from login import load_config

import streamlit as st

config = load_config()

ENDPOINT = config['ENDPOINT']
MODEL = config['gpt_model'] # "gpt-4o"
#PDF = config['invoice_path']
#FOLDER = config['image_folder']
#api_key = config['openai_api_key']


def extract_number(filename):
    # Chercher tous les chiffres dans le nom de fichier et les convertir en entier
    numbers = re.findall(r'\d+', filename)
    return int(numbers[-1]) if numbers else 0

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


def pdf_to_jpg(pdf, output_folder):
    # Creer le dossier automatique de sauvegarde

    os.chmod("content", stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    os.chmod("content/data", stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    os.chmod(output_folder, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    
    #output_folder = "content/data"
    os.makedirs(output_folder, exist_ok=True)

    # Ouvrir le document PDF
    pdf_document = fitz.open(stream=pdf.read(), filetype="pdf")
    
    # Parcourir chaque page du document
    for page_number in range(len(pdf_document)):
        # Sélectionner la page
        page = pdf_document.load_page(page_number)

        # Définir la matrice de transformation pour augmenter la résolution
        # Un zoom de 2x2 double la résolution (200 DPI si l'original est 100 DPI)
        zoomfactor = 5
        matrix = fitz.Matrix(zoomfactor, zoomfactor)
        
        # Extraire l'image de la page
        pix = page.get_pixmap(matrix=matrix)
        # Définir le chemin de sortie pour chaque image
        output_path = f"{output_folder}/page_{page_number + 1}.jpg"
        # Enregistrer l'image
        pix.save(output_path)
        print(f"Page {page_number + 1} enregistrée en tant que {output_path}")
    
    print("Conversion terminée")
    return len(pdf_document)


def chat_HS_code(api_key, prompt):
    headers = {
    "Content-Type": "application/json",
    "api-key": api_key,
    #"Authorization": f"Bearer {api_key}"
    }
    
    payload = {
    "model": MODEL,
    "messages": [
        {
            "role": "system",
            "content": "Tu es un expert en recherche de HS Code, qui aidera les utilisateurs à trouver précisément le HS Code correpondant à la marchandise qu'ils vont te présenter. Réponds uniqument aux questions relatives à la recherche de HS Code."
        },
        {
            "role": "user",
            "content": prompt
        }
    ],
    "temperature": 0.1,
    "top_p": 0.9,
    "max_tokens": 300
    }

    # response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    ENDPOINT = "https://mvd-customgpt-sc.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-02-15-preview"
    response = requests.post(ENDPOINT, headers=headers, json=payload)
    response = response.json()["choices"][0]['message']['content']
    return response



def chat_multi_vision(image_paths, api_key, prompt):
    # Chemins des images
    base64_images = [encode_image(path) for path in image_paths]

    headers = {
    "Content-Type": "application/json",
    "api-key": api_key,
    #"Authorization": f"Bearer {api_key}"
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

    # response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    ENDPOINT = "https://mvd-customgpt-sc.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-02-15-preview"
    response = requests.post(ENDPOINT, headers=headers, json=payload)
    return response



def chat_df(image_paths, api_key, prompt1):
    #prompt1 = GPT_prompt()
    response1 = chat_multi_vision(image_paths, api_key, prompt1)
    table1 = response1.json()["choices"][0]['message']['content']
    
    table1json = table1.split("```json")[1].split("```")[0]
    table1json = table1.split("```json")[1].split("```")[0]
    #st.text(str(table1json))

    json_str_cleaned = table1json.strip().replace('\n', '').replace('Tableau_A=', '').replace("Tableau_A =", '')
    
    
    data = json.loads(json_str_cleaned)
    df = pd.DataFrame(data)

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
    'Poids_total': 'sum',
    'Valeur_totale': 'sum',
    'Montant': 'sum'
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
    'Poids_total': 'sum',
    'Valeur_totale': 'sum',
    'Montant': 'sum'
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
    if code in eu_country_codes:
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
def on_upload_change(change, folder_path):

    os.chmod("content", stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    os.chmod("content/data", stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    os.chmod(folder_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

    if os.path.isdir(folder_path):
        shutil.rmtree(folder_path)
        os.makedirs(folder_path, exist_ok=True)
    else:
        os.makedirs(folder_path, exist_ok=True)

    # images, number_images = convert_pdf_to_images(change)
    number_images = pdf_to_jpg(change,folder_path)

    #images_path = []
    #for img in sorted(glob.glob(folder_path+"/*.jpg")
    #    images_path.append(img)
    #
    #for i, image in enumerate(images):
    #    image_path = os.path.join(folder_path, f'page_{i+1}.jpg')
    #    image.save(image_path, 'JPEG')
    #    images_path.append(image_path)
    #print("TEST", number_images)



def create_overlapping_sublists(image_paths, sublist_size, overlap_size):
    """
    Crée des sous-listes qui se chevauchent à partir d'une liste de chemins d'image.
    
    Parameters:
    image_paths (list): La liste principale des chemins d'image.
    sublist_size (int): Taille de chaque sous-liste.
    overlap_size (int): Nombre d'éléments qui doivent se chevaucher entre les sous-listes.
    
    Returns:
    list: Une liste de sous-listes.
    """
    sublists = []
    for i in range(0, len(image_paths), sublist_size - overlap_size):
        sublists.append(image_paths[i:i + sublist_size])
        if i + sublist_size >= len(image_paths):  # Arrêter si on atteint la fin
            break
    return sublists
