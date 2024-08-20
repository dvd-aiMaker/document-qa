import streamlit as st
from openai import OpenAI

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

from utils import pdf2img, encode_image, pdf_to_jpg, chat_df, on_upload_change, extract_number, create_overlapping_sublists, chat_HS_code
from prompt import GPT_prompt
from build_table import process_df, compute_df, extract_text_from_invoice
from login import load_config, check_login


import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode





# Créer un DataFrame d'exemple
if 'df' not in st.session_state:
    data = {
        'Nom': ['Alice', 'Bob', 'Charlie'],
        'Âge': [24, 19, 32],
        'Ville': ['Paris', 'Lyon', 'Marseille']
    }
    st.session_state.df = pd.DataFrame(data)

# Fonction pour ajouter une ligne
def add_row():
    new_row = pd.Series(["", "", ""], index=st.session_state.df.columns)
    st.session_state.df = st.session_state.df.append(new_row, ignore_index=True)

# Fonction pour supprimer une ligne
def delete_row():
    if not st.session_state.df.empty:
        st.session_state.df = st.session_state.df[:-1]

# Boutons pour ajouter ou supprimer des lignes
col1, col2 = st.columns(2)
with col1:
    if st.button("Ajouter une ligne"):
        add_row()

with col2:
    if st.button("Supprimer la dernière ligne"):
        delete_row()

# Configurer AgGrid pour permettre l'édition
gb = GridOptionsBuilder.from_dataframe(st.session_state.df)
gb.configure_pagination(paginationAutoPageSize=True)  # Optionnel: pagination automatique
gb.configure_side_bar()  # Optionnel: barre latérale avec options de filtrage et de tri
gb.configure_default_column(editable=True)  # Rendre toutes les colonnes éditables
gridOptions = gb.build()

# Afficher le DataFrame avec possibilité d'édition
st.write("Tableau éditable:")
grid_response = AgGrid(
    st.session_state.df,
    gridOptions=gridOptions,
    update_mode=GridUpdateMode.MODEL_CHANGED,  # Met à jour le DataFrame lorsque des modifications sont apportées
    allow_unsafe_jscode=True,  # Permet l'utilisation de JavaScript personnalisé
)

# Obtenir le DataFrame modifié
st.session_state.df = pd.DataFrame(grid_response['data'])

# Afficher le DataFrame modifié
st.write("Tableau modifié:")
st.dataframe(st.session_state.df)

# Optionnel: Traitement supplémentaire ou sauvegarde des modifications
if st.button("Sauvegarder les modifications"):
    st.write("Données sauvegardées:", st.session_state.df)





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

Client_import = ["Bourquin nutrition",
                 "Claval",
                 "Ideal standard",
                 "Maison du monde",
                 "Speno",
                "Contacter votre administrateur pour ajouter un client"]

Client_export = ["", "Agidra", 
                 "Application des gaz",  
                 "Eno", 
                 "Fermob",
                "Grosfillex",
                "Levac",
                "Maison du monde",
                "Rosin",
                "Contacter votre administrateur pour ajouter un client"]



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
        "Téléchargez une facture afin de préparer une déclaration douanière – CustomGPT va vous assister! "
        "Pour utiliser ce logiciel, renseignez la clé API.")
    
    # Ask user for their OpenAI API key via `st.text_input`.
    # Alternatively, you can store the API key in `./.streamlit/secrets.toml` and access it
    # via `st.secrets`, see https://docs.streamlit.io/develop/concepts/connections/secrets-management
    openai_api_key = st.text_input("OpenAI API Key", type="password")
    
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.", icon="🗝️")
    else:
        option_Type_client = st.radio("Sélectionnez une option :", Type_client)

        # Créer une boîte de dialogue dans la barre latérale droite
        with st.sidebar:
            st.header("Assistant HS Code 🔍 ")
            user_input = st.text_input("Demandez votre HS Code...")
            answer_hs_code = chat_HS_code(openai_api_key, str(user_input))
            #answer_hs_code = answer_hs_code.json()["choices"][0]['message']['content']
            if st.button("Recherche"):
                st.write(answer_hs_code)

        
        if option_Type_client =="Régulier":
            option_Type_douane = st.radio("Sélectionnez une option :", Type_douane)
    
            if option_Type_douane=="Export":
                # Ajouter un menu déroulant à l'application
                selection = st.selectbox("Sélectionnez un client :", Client_export)
            elif option_Type_douane=="Import":
                # Ajouter un menu déroulant à l'application
                selection = st.selectbox("Sélectionnez un client :", Client_import)
            else:
                selection = "Ponctuel"
               
        else:
            selection = "Ponctuel"
        
        # Afficher l'option sélectionnée
        st.write(f"Téléchargez la facture du client {selection}")
        
        # Charger un fichier PDF si nécessaire
        uploaded_file = st.file_uploader("Téléchargez la facture comme fichier PDF", type="pdf", accept_multiple_files=True)
        mark = 0


        # Initialisation de l'état de l'application
        if 'extracted_data' not in st.session_state :
            st.session_state.extracted_data = None
            
        if uploaded_file is not None and mark==0:
            print("Le fichier est uploadé!!!!!!")
            
            folder = "content/data"
            on_upload_change(uploaded_file, folder)
            mark+=1
            del uploaded_file
            uploaded_file = None
            st.session_state.uploaded_file = None
        
            image_paths = []
            for img in sorted(glob.glob(folder+"/*jpg"), key=extract_number):
                image_paths.append(img)
                print("image path :", img) 
            
            number_image = len(image_paths)
            st.text("Nombre de page :    "+ str(number_image))
            
            if selection == "Maison du monde":
                DF, DF_SHOW = [], []
                for i in range(len(image_paths)):
                    image_path_i = [image_paths[i]]
                    dfi, df_showi = extract_text_from_invoice(image_path_i ,openai_api_key,selection)
                    DF.append(dfi), DF_SHOW.append(df_showi)
                
                for i in range(len(DF)-1):
                    dfi = DF[i]
                    dfii = DF[i+1]
                    max_id_dfi = dfi['ID'].max()
                    dfii['ID'] = dfii['ID'] + max_id_dfi
                
                df = pd.concat(DF, ignore_index=True)
                df_show = compute_df(df, selection)

                st.text("Valeur Totale: "+ str(df_show['Valeur'].sum()))
                st.text("Poids Total: "+ str(df_show["Poids_total"].sum()))


            else:
                if number_image > 15:
                    #sub_image_paths = create_overlapping_sublists(image_paths, 2, 2)
                    image_paths_1 = image_paths[:(number_image//2) -2]
                    image_paths_2 = image_paths[(number_image//2) -1:]

                    DF, DF_SHOW = [], []
                    df1, df_show1 = extract_text_from_invoice(image_paths_1 ,openai_api_key,selection)
                    df2, df_show2 = extract_text_from_invoice(image_paths_2 ,openai_api_key,selection)

                    # Trouver la valeur maximale de l'ID dans df1
                    max_id_df1 = df1['ID'].max()
                    
                    # Ajuster l'ID dans df2 en ajoutant max_id_df1
                    df2['ID'] = df2['ID'] + max_id_df1
                    
                    df = pd.concat([df1, df2], ignore_index=True)
                    df_show = compute_df(df, selection)

                    st.dataframe(df)
                    st.dataframe(df_show)

                    st.markdown("**Resultat de l'Analyse**")
                    if selection == "Ponctuel":
                        st.text("Valeur Totale: "+ str(df_show['Montant'].sum()))
                        st.text("Poids Total: "+ str(df_show["Poids_total"].sum()))
                    elif selection == "Grosfillex":
                        st.text("Valeur Totale: "+ str(df_show['Valeur'].sum()))
                        st.text("Poids Total: "+ str(df_show["Poids"].sum()))
                    elif selection == "Levac":
                        st.text("Valeur Totale: "+ str(df_show['Montant'].sum()))
                        st.text("Poids Total: "+ str(df_show["Poids_total"].sum()))

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
                    elif selection == "Levac":
                        st.text("Valeur Totale: "+ str(df_show['Montant'].sum()))
                        st.text("Poids Total: "+ str(df_show["Poids_total"].sum()))
                    elif selection == "Maison du monde":
                        st.text("Valeur Totale: "+ str(df_show['Montant'].sum()))
                        st.text("Poids Total: "+ str(df_show["Poids_total"].sum()))
                
            
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

