from flask import Flask, render_template, request, jsonify, session
from jinja2 import Environment, FileSystemLoader
from utils import *
from concurrent.futures import ThreadPoolExecutor
from flask_session import Session

app = Flask(__name__)  # Instanciation application
app.secret_key = "dcvnbljwdncasxpoimkwh"  # Clé pour signer les sessions

env = Environment(loader=FileSystemLoader("templates")) # Initialisation de l'environnement Jinja2 pour charger les templates depuis le dossier "templates"

# Configurer Flask-Session
app.config["SESSION_TYPE"] = "filesystem"  # Utiliser un système de fichiers pour le stockage des sessions
app.config["SESSION_FILE_DIR"] = "./flask_session/"  # Définir le répertoire où les données de session seront stockées
app.config["SESSION_FILE_THRESHOLD"] = 500  # Définir le nombre maximum de fichiers de session qui seront conservés
Session(app)  # Initialiser Flask-Session avec l'application


# Page d'accueil
@app.route("/", methods=["GET", "POST"])
def admin():
    return render_template("admin.html")


# Génération plan de formation
@app.route("/plan", methods=["POST"])
def plan():
    # Variables de session: plan et sujet de la formation
    session["subject"] = request.get_json()["subject"]
    session["training-plan"] = {}

    prompt = prompt_plan(session['subject'])  # Génération prompt plan 
    response_gpt = gpt_request(prompt)  # Requête GPT Génération plan de formation

    session["training-plan"], training_plan_html = format_plan(response_gpt)  # Formattage plan de formation: dictionaire et html

    return jsonify(training_plan=training_plan_html)


@app.route("/modify", methods=["POST"])
def modify():
    training_plan = request.get_json()["training_plan"]  # Récupération du plan de formation html
    modification_requests = request.get_json()["modification_requests"]  # Récupération demande de modifications du plan
    
    new_plan = modify_training_plan(training_plan, modification_requests)  # Requête GPT modification plan
    session["training-plan"]=html_to_dict(new_plan)  # Stockage du nouveau plan en dict dans la variable de session
    
    return jsonify(modified_plan=new_plan)


@app.route("/generate", methods=["POST"])
def generate():
    session["all-content"] = {}  # Variable de session pour stocker le contenu de chaque section (dict: nom de session, contenu)

    # Threads pour générer le contenu (requêtes GPT) de manière simultanée
    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(
                generate_content_for_section, section, subsections, session["subject"], convert_training_plan_to_text(session["training-plan"])
            ): section
            for section, subsections in session["training-plan"].items()
        }

    # Ajout du contenu généré dans le dictionnaire une fois que tous les threads sont terminés
    for future in futures:
        section = futures[future]
        session["all-content"][section] = future.result()

    # Nettoyage du dictionnaire (suppression des espaces superflus et des "\n")
    session["all-content"] = clean_content(session["all-content"])

    return jsonify(success=True, all_content=list(session["all-content"].keys()))


@app.route("/verify", methods=["GET"])
def verify():
    section = request.args.get("section")  # Récupération de la section a afficher

    # Si la section n'est pas une clé du dict avec toutes les sections et les contenus, retourner une erreur
    if section is None or section not in session["all-content"]:
        return "Invalid section", 400
    
    content = session["all-content"][section] #  Récupération du contenu de la section en question

    return render_template("verify.html", section_content=content)


@app.route('/modify_content', methods=['POST'])
def modify_content():  
    current_content = request.get_json()['current_content'] #  Récupération contenu html
    modification_requests = request.get_json()['modification_requests'] #  Récupération demande de modifications du contenu
    section_title = request.get_json()['section_title']  # Récupération du titre de la section en question
    
    new_content = modify_content_gpt(current_content, modification_requests) # Requête GPT modification contenu
    session['all-content'][section_title] = new_content # Stockage du nouveau contenu dans le dict de tous les contenus
    
    return jsonify(modified_content = new_content)


@app.route('/valider', methods=['POST'])
def valider(): 
    # Génération de la descrption de la formation
    prompt = f"""Fournis une description concise de {session["subject"]}, en 20-25 mots maximum"""

    session["description"]  = gpt_request(prompt)

    # Ajout de la formation sur le site
    handle_github(session["subject"], session["description"], session["training-plan"],session["all-content"])

    # Retournez une confirmation
    return jsonify({"success": True})


# Lance l'application lors de l'éxcécution du programme
if __name__ == '__main__':
    app.run(debug=True)