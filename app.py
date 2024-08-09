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

# Show title and description.
st.title("📄 CustomSmart")
st.write(
    "Télécharge une facture afin de faire une déclaration douanière – CustomGPT va t'assister! "
    "Pour utiliser ce logiciel, renseignes la clé API.")

# Ask user for their OpenAI API key via `st.text_input`.
# Alternatively, you can store the API key in `./.streamlit/secrets.toml` and access it
# via `st.secrets`, see https://docs.streamlit.io/develop/concepts/connections/secrets-management
openai_api_key = st.text_input("OpenAI API Key", type="password")

if not openai_api_key:
    st.info("Please add your OpenAI API key to continue.", icon="🗝️")
#else:

# Menu déroulant
Client = ["Grosfillex", "Ponctuel"]

# Ajouter un menu déroulant à l'application
selection = st.selectbox("Sélectionnez un client :", Client)

# Afficher l'option sélectionnée
st.write(f"Téléchargez la facture du client {selection}")

# Charger un fichier PDF si nécessaire
uploaded_file = st.file_uploader("Téléchargez la facture comme fichier PDF", type="pdf")

