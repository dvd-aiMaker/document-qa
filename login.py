import json

# Fonction pour charger le fichier de configuration
def load_config():
    with open("config.json", "r") as file:
        config = json.load(file)
    return config

# Fonction pour vérifier les identifiants
def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter"):
        if username in users and users[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
        else:
            st.error("Nom d'utilisateur ou mot de passe incorrect.")
