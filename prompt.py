def GPT_prompt(client):
    if client == "Ponctuel":
        prompt1 = "Construit un Tableau A au format json pour chaque marchandise ligne par ligne trouvée dans les factures. Attention il faut bien prendre en compte ligne par ligne, il peut y avoir des duplicatas qu'il faut considérer indépendamment. Chacune des lignes sera attribuée à un ID, et la colonne ID sera en première position dans le Tableau A."
        prompt1 += "\n\n"
        prompt1 += " Ajoutes une clé correspondant à la Designation. Cette valeur correspond à la description de la marchandise."
        prompt1 += " Ajoutes une clé correspondant au Code Douane. La valeur est une suite numérique de taille à 8 chiffres qui précède l'indication pays (comme par exemple FR). Attention il ne faut pas confondre avec la Référence Client ou le Code EAN."
        prompt1 += " Si le code douane que tu as rapporté de la facture n'est pas un code à 8 chiffres, tu t'es trompé et tu dois trouver dans la facture le code douane dans la colonne 'Désignation'."
        prompt1 += " Si il n'y a aucun code douane de mentionné dans la facture, à partir de la designation tu dois aller le chercher sur cette page internet: https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=OJ:L:2021:385:FULL "
        prompt1 += " Ajoutes une clé correspondant à l'Origine, la valeur doit être donnéee en ISO 3166-1 alpha-2."
        prompt1 += " Ajoutes une clé correspondant à la Valeur, ceci correspond à la valeur unitaire, et la valeur doit être repporté comme un float."
        prompt1 += " Ajoutes une clé correspondant au Montant, celui ci prend en compte la quantité et peut être remisé."
        prompt1 += " Ajoutes une clé correspondant à la Valeur Douane, met 0 si la clé correspond à la Valeur est non nul, sinon il faut mettre la valeur douane EUR renseigné dans la description."
        prompt1 += " Ajoutes une clé correspondant au Poids. Cette valeur doit être repporté comme un float."
        prompt1 += " Ajoutes une clé correspondant aux Quantités. Cette valeur se trouve dans la colonne 'Qté livrée' et doit être repporté comme un float."

    elif client == "Grosfillex":
        prompt1 = "Construit un Tableau A au format json pour chaque marchandise ligne par ligne trouvée dans les factures. Attention il faut bien prendre en compte ligne par ligne, il peut y avoir des duplicatas qu'il faut considérer indépendamment. Chacune des lignes sera attribuée à un ID, et la colonne ID sera en première position dans le Tableau A."
        prompt1 += "\n\n"
        prompt1 += " Ajoutes une clé correspondant à la Designation. Cette valeur correspond à la description de la marchandise."
        prompt1 += " Ajoutes une clé correspondant au Code Douane. La valeur est une suite numérique de taille à 8 chiffres qui précède l'indication pays (comme par exemple FR). Attention il ne faut pas confondre avec la Référence Client ou le Code EAN."
        prompt1 += " Si le code douane que tu as rapporté de la facture n'est pas un code à 8 chiffres, tu t'es trompé et tu dois trouver dans la facture le code douane dans la colonne 'Désignation'."
        prompt1 += " Si il n'y a aucun code douane de mentionné dans la facture, à partir de la designation tu dois aller le chercher sur cette page internet: https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=OJ:L:2021:385:FULL "
        prompt1 += " Ajoutes une clé correspondant à l'Origine, la valeur doit être donnéee en ISO 3166-1 alpha-2."
        prompt1 += " Ajoutes une clé correspondant à la Valeur, et la valeur doit être repporté comme un float."
        prompt1 += " Ajoutes une clé correspondant au Montant, celui ci prend en compte la quantité et peut être remisé."
        prompt1 += " Ajoutes une clé correspondant à la Valeur Douane, met 0 si la clé correspond à la Valeur est non nul, sinon il faut mettre la valeur douane EUR renseigné dans la description."
        prompt1 += " Ajoutes une clé correspondant au Poids. Cette valeur doit être repporté comme un float."
        prompt1 += " Ajoutes une clé correspondant aux Quantités, et la valeur doit être repporté comme un float."


        
    prompt1 += "\n\n La réponse ne doit contenir que le Tableau A comme suit : Tableau_A=[{ "

    return prompt1
