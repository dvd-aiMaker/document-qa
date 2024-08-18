from prompt import GPT_prompt
from utils import chat_df

import pandas as pd

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



def process_df(df, selection):
  if "Code_Douane" not in df.columns and "Code Douane" in df.columns:
    df.rename(columns={"Code Douane": "Code_Douane"}, inplace=True)
  if "Code_Douane" not in df.columns and "CodeDouane" in df.columns:
      df.rename(columns={"CodeDouane": "Code_Douane"}, inplace=True)
  
  if selection == "Ponctuel":
    if "Valeur_Douane" not in df.columns and "Valeur Douane" in df.columns:
      df.rename(columns={"Valeur Douane": "Valeur_Douane"}, inplace=True)

    df['Poids_total'] = df['Poids'] * df['Quantités']
    # Création de la nouvelle colonne Valeur_totale
    df['Valeur_totale'] = df.apply(lambda row: row['Valeur'] * row['Quantités'] if row['Valeur'] != 0 else row['Valeur_Douane'] * row['Quantités'], axis=1)
    
    df['Valeur'] = pd.to_numeric(df['Valeur'], errors='coerce')
    df["Poids_total"] = pd.to_numeric(df['Poids_total'], errors='coerce')
    
  elif selection == "Grosfillex":

    df['Valeur'] = pd.to_numeric(df['Valeur'], errors='coerce')
    df["Poids"] = pd.to_numeric(df['Poids'], errors='coerce')
  
  elif selection == "Levac":
    if "Valeur_Douane" not in df.columns and "Valeur Douane" in df.columns:
      df.rename(columns={"Valeur Douane": "Valeur_Douane"}, inplace=True)

    df['Poids_total'] = df['Poids'] * df['Quantités']
    # Création de la nouvelle colonne Valeur_totale
    df['Valeur_totale'] = df.apply(lambda row: row['Valeur'] * row['Quantités'] if row['Valeur'] != 0 else row['Valeur_Douane'] * row['Quantités'], axis=1)
    
    df['Valeur'] = pd.to_numeric(df['Valeur'], errors='coerce')
    df["Poids_total"] = pd.to_numeric(df['Poids_total'], errors='coerce')

    
  else:
    print("Le client n'est pas dans la base")
  return df

def compute_df(df, selection):
  if selection == "Ponctuel":
    return compute_df_Ponctuel(df)
  elif selection == "Grosfillex":
    return compute_df_Grosfillex(df)
  elif selection == "Levac":
    return compute_df_Levac(df)
  else:
    print(selection + "is Not ready")


def compute_df_Ponctuel(df):
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


def compute_df_Grosfillex(df):
  # Création de la DataFrame pour les origines EU
  df_eu = df[df['Origine'].isin(eu_country_codes)]
  

  # Agrégation des données par code douanier pour les origines EU
  df_eu_aggregated = df_eu.groupby('Code_Douane').agg({
      'ID': lambda x: list(x),
      'Valeur': 'sum',
      'Poids': 'sum'
  }).reset_index()
  df_eu_aggregated["ORIGINE"] = "EU"


  # Création de la DataFrame pour les origines hors EU
  df_non_eu = df[~df['Origine'].isin(eu_country_codes)]
  

  # Agrégation des données par code douanier pour les origines hors EU
  df_non_eu_aggregated = df_non_eu.groupby('Code_Douane').agg({
      'ID': lambda x: list(x),
      'Valeur': 'sum',
      'Poids': 'sum'
  }).reset_index()
  df_non_eu_aggregated["ORIGINE"] = "HORS EU"


  # Concaténation des deux DataFrames
  df_combined = pd.concat([df_eu_aggregated, df_non_eu_aggregated], ignore_index=True)
  return df_combined


def compute_df_Levac(df):
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


def extract_text_from_invoice(image_paths, api_key, selection):
  df = chat_df(image_paths, api_key, GPT_prompt(selection))
  df = process_df(df, selection)
  df_show = compute_df(df, selection)
  return df, df_show
