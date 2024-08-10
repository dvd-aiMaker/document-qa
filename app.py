import streamlit as st
from openai import OpenAI
import os

from PIL import Image
import io

import json
import os
import requests
from openai import OpenAI
import pandas as pd
import glob
import time

from pdf2image import convert_from_path
import shutil
from pathlib import Path
import base64

import fitz  # PyMuPDF

from utils import pdf2img, encode_image, pdf_to_jpg, chat_df, compute_df, on_upload_change

from prompt import GPT_prompt

Type_client = ["Régulier", "Ponctuel"]
Type_douane = ["Import", "Export"]
Client = ["Grosfillex", ""]


# Show title and description.
st.title("📄 CustomSmart")
st.write(
    "Téléchargez une facture afin de faire une déclaration douanière – CustomGPT va vous assister! "
    "Pour utiliser ce logiciel, renseignez la clé API.")

# Ask user for their OpenAI API key via `st.text_input`.
# Alternatively, you can store the API key in `./.streamlit/secrets.toml` and access it
# via `st.secrets`, see https://docs.streamlit.io/develop/concepts/connections/secrets-management
openai_api_key = st.text_input("OpenAI API Key", type="password")

if not openai_api_key:
    st.info("Please add your OpenAI API key to continue.", icon="🗝️")
else:
    # Proposer à l'utilisateur de choisir entre "Import" et "Export"
    option_Type_client = st.radio("Sélectionnez une option :", Type_client)

    if option_Type_client =="Régulier":
        # Ajouter un menu déroulant à l'application
        selection = st.selectbox("Sélectionnez un client :", Client)

        # Proposer à l'utilisateur de choisir entre "Import" et "Export"
        option_Type_douane = st.radio("Sélectionnez une option :", Type_douane)
        print("BUG" ,option_Type_douane)
        
    else:
        selection = "Ponctuel"
    
    # Afficher l'option sélectionnée
    st.write(f"Téléchargez la facture du client {selection}")
    
    # Charger un fichier PDF si nécessaire
    uploaded_file = st.file_uploader("Téléchargez la facture comme fichier PDF", type="pdf")

    if uploaded_file != None:

        folder = "content/data"
        on_upload_change(uploaded_file,folder)
    
        image_paths = []
        for img in sorted(glob.glob(folder+"/*jpg")):
            image_paths.append(img)
            print("image path :",img ) 
    
        print("Extraction is starting from invoice")
        df = chat_df(image_paths, openai_api_key, GPT_prompt())
        df_show = compute_df(df)
    
        df_show["Valeur_totale"] = df_show["Valeur"] + df_show["Valeur_Douane"]
    
        df_show['Valeur'] = pd.to_numeric(df_show['Valeur'], errors='coerce')
        df_show["Poids_total"] = pd.to_numeric(df_show['Poids_total'], errors='coerce')
    
        print("\n\n TABLEAU LISTE MARCHANDISE:")
        print(df)
    
        print("\n\n RESULTAT TABLEAU AGREGE:")
        print(df_show)
        print("Valeur Totale: ", df_show['Valeur'].sum())
        print("Poids Total: ", df_show["Poids_total"].sum())
    
    
        print("\n\n ANALYSE:")
        # Filtrage des lignes où Valeur et Valeur_Douane sont nulles
        filtered_df = df[(df['Valeur'] == 0.0) & (df['Valeur_Douane'] == 0.0)]
        # Extraction des IDs correspondants
        ids = filtered_df['ID'].tolist()
        # Affichage des IDs
        print("Anomalies aux IDs :", ids, "-> Les Valeur et Valeur_Douane sont nulles")



