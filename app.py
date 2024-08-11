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
from datetime import datetime

from pdf2image import convert_from_path
import shutil
from pathlib import Path
import base64

import fitz  # PyMuPDF

from utils import pdf2img, encode_image, pdf_to_jpg, chat_df, on_upload_change, extract_number, create_overlapping_sublists
from prompt import GPT_prompt
from build_table import process_df, compute_df, extract_text_from_invoice
from login import load_config, check_login



# ----- CONNEXION 
# Charger les utilisateurs et mots de passe à partir du fichier de configuration
config = load_config()
users = config["users"]

connect = False

if connect == False:
    # Vérification de l'état de connexion
    if not st.session_state.get("logged_in"):
        st.warning("Veuillez vous connecter pour accéder à l'application.")
        st.image("image/vuaillat.jpg", use_column_width=True)
        check_login(users)
        connect = True
    
    else:
        st.success(f"Bienvenue {st.session_state.username} !")
        # Afficher le contenu de l'application ici
        st.write("Vous êtes connecté et pouvez maintenant accéder à l'application.")
        connect = True
        
        # Ajouter un bouton de déconnexion
        if st.button("Se déconnecter"):
            st.session_state.logged_in = False
            st.experimental_rerun()

# -----


Type_client = ["Ponctuel", "Régulier"]
Type_douane = ["Import", "Export"]
Client = ["","Grosfillex"]

# # Injecter du CSS pour changer la couleur de fond
# st.markdown(
#     """
#     <style>
#     /* Changer la couleur de tout le texte en vert */
#     .stApp {
#         color: green;
#         background-color: #f5f5dc; /* Fond beige */
#     }
#     /* Changer la couleur des titres */
#     .stApp h1, .stApp h2, .stApp h3 {
#         color: darkgreen; /* Couleur plus foncée pour les titres */
#     }
#     </style>
#     """,
#     unsafe_allow_html=True
# )

# # Injecter du CSS pour changer la couleur du texte en vert
# st.markdown(
#     """
#     <style>
#     /* Changer la couleur de tout le texte en vert */
#     .stApp {
#         color: green;
#     }
#     </style>
#     """,
#     unsafe_allow_html=True
# )

if st.session_state.get("logged_in"):
    st.image("image/vuaillat.jpg", use_column_width=True)
    
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
        option_Type_client = st.radio("Sélectionnez une option :", Type_client)
    
        if option_Type_client =="Régulier":
            option_Type_douane = st.radio("Sélectionnez une option :", Type_douane)
    
            if option_Type_douane=="Export":
                # Ajouter un menu déroulant à l'application
                selection = st.selectbox("Sélectionnez un client :", Client)
            elif option_Type_douane=="Import":
                # Ajouter un menu déroulant à l'application
                selection = st.selectbox("Sélectionnez un client :", Client)
            else:
                selection = "Ponctuel"
               
        else:
            selection = "Ponctuel"
        
        # Afficher l'option sélectionnée
        st.write(f"Téléchargez la facture du client {selection}")
        
        # Charger un fichier PDF si nécessaire
        uploaded_file = st.file_uploader("Téléchargez la facture comme fichier PDF", type="pdf")
        mark = 0
        
        if uploaded_file != None and mark==0:
            print("Le fichier est uploadé!!!!!!")
            
            folder = "content/data"
            on_upload_change(uploaded_file, folder)
            mark+=1
        
            image_paths = []
            for img in sorted(glob.glob(folder+"/*jpg"), key=extract_number):
                image_paths.append(img)
                print("image path :", img) 
            
            number_image = len(image_paths)
            st.text("BUGGGG    "+ number_image)

            if number_image > 15:
                sub_image_paths = create_overlapping_sublists(image_paths, 2, 2)

                DF, DF_SHOW = [], []
                print("Extraction is starting from invoice")
                for i in range(len(sub_image_paths)):
                    sublist = sub_image_paths[i]
                    df, df_show = extract_text_from_invoice(sublist,openai_api_key,selection)
                    DF.append(df), DF_SHOW.append(df_show)

                DF, DF_SHOW = [], []
                print("Extraction is starting from invoice")
                for i in range(len(sub_image_paths)):
                    sublist = sub_image_paths[i]
                    df, df_show = extract_text_from_invoice(sublist,openai_api_key,selection)
                    DF.append(df), DF_SHOW.append(df_show)

                for i in range(len(sub_image_paths)):
                    st.dataframe(DF[i])
                    st.dataframe(DF_SHOW[i])
            else:
                df, df_show = extract_text_from_invoice(image_paths ,openai_api_key,selection)
                st.dataframe(df)
                st.dataframe(df_show)

                st.markdown("**Resultat de l'Analyse**")
                if selection == "Ponctuel":
                    st.text("Valeur Totale: "+ str(df_show['Montant'].sum()))
                    st.text("Poids Total: "+ str(df_show["Poids_total"].sum()))
                elif selection == "Grosfillex":
                    st.text("Valeur Totale: "+ str(df_show['Valeur'].sum()))
                    st.text("Poids Total: "+ str(df_show["Poids"].sum()))
                

            
            #df, df_show = extract_text_from_invoice(image_paths,openai_api_key,selection)
            # df = chat_df(image_paths, openai_api_key, GPT_prompt(selection))
            # df = process_df(df, selection)
            # df_show = compute_df(df, selection)
        
            # df_show["Valeur_totale"] = df_show["Valeur"] + df_show["Valeur_Douane"]
        
            # df_show['Valeur'] = pd.to_numeric(df_show['Valeur'], errors='coerce')
            # df_show["Poids_total"] = pd.to_numeric(df_show['Poids_total'], errors='coerce')
        


            

            # print("\n\n TABLEAU LISTE MARCHANDISE:")
            # st.dataframe(df)
        
            # print("\n\n RESULTAT TABLEAU AGREGE:")
            # st.dataframe(df_show)
    
            # st.markdown("**Resultat de l'Analyse**")
            # if selection == "Ponctuel":
            #     st.text("Valeur Totale: "+ str(df_show['Montant'].sum()))
            #     st.text("Poids Total: "+ str(df_show["Poids_total"].sum()))
            # elif selection == "Grosfillex":
            #     st.text("Valeur Totale: "+ str(df_show['Valeur'].sum()))
            #     st.text("Poids Total: "+ str(df_show["Poids"].sum()))

