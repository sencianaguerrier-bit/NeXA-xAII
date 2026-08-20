import re
import requests
import streamlit as st

# Clé API Groq configurée
GROQ_API_KEY = "Gsk_nALGqqF9YTlFwYHmiv60WGdyb3FYHH1TSE3xR7ZrGW2x5LfGeM0t"

def romain_vers_int(romain):
    valeurs = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100}
    total, prev = 0, 0
    for char in reversed(romain):
        val = valeurs.get(char, 0)
        total += val if val >= prev else -val
        prev = val
    return total

def interroger_groq(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }
    payload = {
        "messages": [
            {"role": "system", "content": "Tu es Nexa AI. Tu réponds de manière intelligente, naturelle, vivante et fluide, exactement comme Gemini."},
            {"role": "user", "content": prompt}
        ],
        "model": "llama-3.3-70b-versatile",
        "temperature": 0.7
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        return f"Erreur API ({response.status_code}) : {response.text}"
    except Exception as e:
        return f"Erreur de connexion : {str(e)}"

def lexer(code):
    tokens = []
    regex_rules = [
        ('ACCOLADE_OUV', r'\{'),
        ('ACCOLADE_FERM', r'\}'),
        ('EGAL', r'='),
        ('PLUS', r'\+'),
        ('POINT_VIRGULE', r';'),
        ('ROMAIN', r'\b[IVXC]+\b'),
        ('MOT_CLE', r'\b(VAR|NEXA|ASK_NEXA)\b'),
        ('TEXTE', r'"[^"]*"'),
        ('IDENTIFIANT', r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'),
        ('SKIP', r'[ \t\n]+'),
    ]
    pos = 0
    while pos < len(code):
        match = None
        for type_token, regex in regex_rules:
            pattern = re.compile(regex)
            match = pattern.match(code, pos)
            if match:
                valeur = match.group(0)
                if type_token != 'SKIP':
                    tokens.append((type_token, valeur))
                pos = match.end()
                break
        if not match:
            raise SyntaxError(f"Caractère inconnu : {code[pos]}")
    return tokens

class InterpreteurK:
    def __init__(self):
        self.variables = {}
        self.outputs = []

    def executer(self, tokens):
        i = 0
        while i < len(tokens):
            type_t, val_t = tokens[i]

            if type_t == 'MOT_CLE' and val_t == 'VAR':
                var_name = tokens[i+1][1]
                i += 3 
                valeur = self.evaluer_expression(tokens, i)
                self.variables[var_name] = valeur
                while tokens[i][0] != 'POINT_VIRGULE':
                    i += 1

            elif type_t == 'MOT_CLE' and val_t == 'NEXA':
                i += 1
                type_expr, val_expr = tokens[i]
                if type_expr == 'TEXTE':
                    self.outputs.append(("system", f"[NEXA System]: {val_expr[1:-1]}"))
                elif type_expr == 'IDENTIFIANT':
                    val = self.variables.get(val_expr, 'Inconnue')
                    self.outputs.append(("system", f"[NEXA System]: Variable {val_expr} = {val}"))
                while tokens[i][0] != 'POINT_VIRGULE':
                    i += 1

            elif type_t == 'MOT_CLE' and val_t == 'ASK_NEXA':
                i += 1
                type_expr, val_expr = tokens[i]
                prompt = val_expr[1:-1] if type_expr == 'TEXTE' else str(self.variables.get(val_expr, ""))
                
                self.outputs.append(("user", prompt))
                reponse = interroger_groq(prompt)
                self.outputs.append(("ai", reponse))
                
                while tokens[i][0] != 'POINT_VIRGULE':
                    i += 1

            i += 1

    def evaluer_expression(self, tokens, index):
        total = 0
        while tokens[index][0] != 'POINT_VIRGULE':
            type_t, val_t = tokens[index]
            if type_t == 'ROMAIN':
                total += romain_vers_int(val_t)
            elif type_t == 'IDENTIFIANT':
                total += self.variables.get(val_t, 0)
            index += 1
        return total

# --- DESIGN STREAMLIT ---
st.set_page_config(page_title="Nexa AI Studio", page_icon="✨", layout="centered")

# CSS personnalisation boutons et interface
st.markdown("""
<style>
    .stButton>button {
        background: linear-gradient(90deg, #4F46E5 0%, #7C3AED 100%);
        color: white;
        border-radius: 12px;
        padding: 10px 24px;
        font-weight: bold;
        border: none;
        box-shadow: 0 4px 14px 0 rgba(124, 58, 237, 0.39);
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #4338CA 0%, #6D28D9 100%);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

st.title("✨ Nexa AI Studio — Language K")

tabs = st.tabs(["💬 Chatbot Direct", "📜 Éditeur Language K"])

# TAB 1: Chatbot interactif avec Micro + Texte
with tabs[0]:
    st.subheader("Discutez avec Nexa AI")
    
    # Entrée vocale (Audio)
    audio_val = st.audio_input("🎙️ Appuyez pour parler à Nexa")
    
    # Entrée Chat classique
    user_prompt = st.chat_input("Écrivez votre message à Nexa...")
    
    if user_prompt:
        st.chat_message("user").write(user_prompt)
        with st.spinner("Nexa réfléchit..."):
            reponse = interroger_groq(user_prompt)
            st.chat_message("assistant", avatar="✨").write(reponse)

# TAB 2: Exécution de code K
with tabs[1]:
    st.subheader("Console Language K")
    code_exemple = """{
    NEXA "Système prêt.";
    VAR valeur = X + V;
    NEXA valeur;
    
    ASK_NEXA "Présente-toi avec style et énergie !";
}"""
    
    code_input = st.text_area("Code K :", value=code_exemple, height=200)
    
    if st.button("🚀 Exécuter le code Language K"):
        try:
            tokens = lexer(code_input)
            interpreteur = InterpreteurK()
            interpreteur.executer(tokens)
            
            for type_msg, message in interpreteur.outputs:
                if type_msg == "system":
                    st.code(message)
                elif type_msg == "user":
                    st.write(f"**🗣️ Question :** {message}")
                elif type_msg == "ai":
                    st.success(f"**✨ Nexa AI :**\n\n{message}")
        except Exception as e:
            st.error(f"Erreur : {e}")
                          
