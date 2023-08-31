import openai
import re
import subprocess
import os
import tempfile
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from urllib.parse import quote
from jinja2 import Environment, FileSystemLoader


# Génération du prompt pour le plan
def prompt_plan(subject):
    prompt = f"""Tu es un expert en création de contenu e-learning {subject}. Ton défi: élaborer un plan de formation e-learning en {subject} qui pourrait être vendu sur les plateformes professionnelles. 
    La formation doit être un produit de qualité professionnelle, extrêmement complète et aborder tous les angles du sujet, du niveau débutant au niveau expert. 
    Attention : la structure est cruciale. Le plan doit être organisé en sections numérotées (Section 1., Section 2., Section 3., ...). 
    Chaque section doit avoir des sous-sections numérotées (1.1, 1.2, 1.3, ..., 2.1, 2.2, 2.3, ...). 
    Les supports pédagogiques seront principalement du texte et des exemples de code. 
    Vise l'exhaustivité : ne néglige aucun élément crucial du {subject} et inclut toutes les facettes, techniques, concepts, pratiques et exemples nécessaires pour une compréhension complète.
    Sépare bien la formation en plusieurs sections et sous-section afin de couvrir l'entièreté du sujet.
    Ecris uniquement des titres de sections et sous-sections. Le respect de cette structure est impératif. Aucun autre texte n'est nécessaire."""

    return prompt


# Requête Open AI
def gpt_request(prompt):
    openai.api_key = "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"

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    response = completion["choices"][0]["message"]["content"]

    return response


# Formattage plan répionse Open AI en dict et html
def format_plan(response_gpt):
    response_list = response_gpt.split("\n")
    training_plan = {}

    for line in response_list:
        # Si la ligne commence par 'Section'
        if re.match(r"Section", line):
            # Sélection titre section et ajout dictionnaire
            section = line
            training_plan[section] = []
        # Si la ligne commence par un nombre (= sous-section)
        elif re.match(r"\d+\.\d+", line):
            # Sélection titre sous-section et ajout dictionnaire (clé = section en cours)
            subsection = re.sub(r"\d+\.\d+ ", "", line)
            training_plan[section].append(subsection)

    # Mise en forme html
    training_plan_html = ""
    for section in training_plan:
        training_plan_html += f"<h3>{section}</h3><ul>"
        for subsection in training_plan[section]:
            training_plan_html += f"<li>{subsection}</li>"
        training_plan_html += "</ul><br>"

    return training_plan, training_plan_html


# Modification du plan
def modify_training_plan(training_plan, modification_requests):
    modification_message = f"""Voici le plan de formation actuel : {training_plan}.
                               Je souhaite apporter les modifications suivantes : {modification_requests}.
                               Veuillez inclure le plan de formation complet avec ces modifications."""

    # Utilisation de la fonction gpt_request() pour obtenir la réponse
    response = gpt_request(modification_message)

    start_index = response.find("<h3>")
    modified_plan = response[start_index:]

    return modified_plan


# Conversion plan html en dict (clé=sections, contenu=sous-sections)
def html_to_dict(text):
    sections = re.findall(r'<h3>(.*?)<\/h3>', text)
    lists = re.findall(r'<ul>(.*?)<\/ul>', text, re.DOTALL)

    result = {}

    for section, list_content in zip(sections, lists):
        items = re.findall(r'<li>(.*?)<\/li>', list_content)
        result[section] = items

    return result


# Conversion du plan de formation dict en texte
def convert_training_plan_to_text(training_plan):
    plan_text = ""
    for section, subsections in training_plan.items():
        plan_text += f"Section: {section}\n"
        for i, subsection in enumerate(subsections):
            plan_text += f"  Sous-section {i+1}: {subsection}\n"
    return plan_text.strip()


def generate_content_for_section(section, subsections, subject, training_plan_text):
    prompt = f"""Tu es un expert en création de contenu e-learning {subject}. Ton défi : créer un contenu qui atteint un niveau de qualité professionnelle, similaire à ce qui est vendu dans l'industrie du e-learning.
                Le plan complet de la formation est le suivant : {training_plan_text}
                Écris le contenu de la section {section} de ma formation e-learning {subject} en utilisant les balises HTML appropriées. 
                Pour la section {section}, utilise la balise <h1>. Pour les sous-sections {', '.join(subsections)}, utilise la balise <h2>, sans ajouter "Sous-section X:" avant le nom de la sous-section.
                Ce contenu doit être très détaillé, ne laissant aucune question sans réponse. Inclut des descriptions précises, des explications en profondeur et des exemples/codes lorsque cela est pertinent.
                Les exemples doivent toujours aller avec des explications détailées et complètes.
                Les paragraphes de texte doivent être encadrés par la balise <p> et les blocs de code par les balises <pre><code>, exactement comme dans l'exemple suivant :
                <pre><code>i = 0;

                    while (!deck.isInOrder()) {{
                        print 'Iteration ' + i;
                        deck.shuffle();
                        i++;
                    }}

                    print 'It took ' + i + ' iterations to sort the deck.';
                </code></pre>
                Assure-toi de fournir des informations précises, complètes et vérifiées. N'ajoute aucun texte autre que celui de la formation."""

    response = gpt_request(prompt)

    return response


# Modification du contenu
def modify_content_gpt(current_content, modification_requests):
    modification_message = f"""Voici le contenu actuel : {current_content}.
                            Je souhaite apporter les modifications suivantes : {modification_requests}.
                            Veuillez inclure le contenu complet avec ces modifications."""

    # Utilisation de la fonction gpt_request() pour obtenir la réponse
    response = gpt_request(modification_message)

    start_index = response.find("<h1>")
    modified_content = response[start_index:]

    return modified_content


# Nettoyer contenu dictionnaire (espaces et sauts de lignes inutiles)
def clean_content(content_dict):
    cleaned_dict = {}
    for key, value in content_dict.items():
        # cleaned_value = value.replace('\n', '')
        cleaned_value = value.strip()
        cleaned_dict[key] = cleaned_value
    return cleaned_dict


# Générer la table des matières de la formaiton (html)
def generate_html(sections):
    html = []

    for section, sub_sections in sections.items():
        section_num, section_title = section.split('. ', 1)
        href = section_num
        html.append('<li><a href="{}">{}</a>'.format(href, section))

        sub_section_lines = []
        for sub_title in sub_sections:
            sub_section_lines.append(sub_title)

        sub_section_text = '<br>\n\t\t\t\t'.join(sub_section_lines)
        html.append('\t<ul>{}\n\t\t\t\t</ul>'.format(sub_section_text))

        html.append('</li>')

    return '\n'.join(html)


# Générer l'image pour les formation (avec le titre)
def generate_image(subject, repo_path):
    # Paramètres de l'image
    image_width = 1000
    image_height = 250
    font_size = 120
    text = subject
    font_path = "static/KaushanScript-Regular.ttf"
    text_color = (255, 255, 255, 255)
    bg_color = (66, 71, 84, 255)

    # Création de l'image
    image = Image.new('RGBA', (image_width, image_height), bg_color)
    font = ImageFont.truetype(font_path, font_size)
    draw = ImageDraw.Draw(image)
    text_width, text_height = draw.textsize(text, font)
    x = (image_width - text_width) / 2
    y = (image_height - text_height) / 2
    y -= 12
    draw.text((x, y), text, fill=text_color, font=font)

    # Sauvegarder l'image dans le dossier du dépôt GitHub
    output_path = os.path.join(repo_path, 'images', f"{subject.lower()}.png")
    image.save(output_path)


# Extraction du numéro de section
def extract_section_id(text):
    # Chercher le numéro à l'aide d'une expression régulière
    match = re.search(r"Section (\d+)", text)
    if match:
        return f"section{match.group(1)}"
    else:
        return None


# Ajout de la formation dans la page qui conteint toutes les formations
def modify_html(file_path, subject, description):
    # Lire le contenu du fichier
    with open(file_path, 'r') as file:
        content = file.read()

    soup = BeautifulSoup(content, 'html.parser')

    # Encoder le sujet pour une utilisation dans les URL et les noms de fichier
    subject_lower_encoded = quote(subject.lower())
    new_article = BeautifulSoup(f'''
    <article>
        <a href="AI-Learning/{subject_lower_encoded}/{subject_lower_encoded}.html" class="image"><img src="images/{subject_lower_encoded}.png" alt="" /></a>
        <h3 class="major" style="display:none;">{subject}</h3>
        <p>{description}</p>
        <a href="AI-Learning/{subject_lower_encoded}/{subject_lower_encoded}.html" class="special">Commencer la formation</a>
    </article>
    ''', 'html.parser')

    articles = soup.find_all('article')

    # Vérifier si le sujet existe déjà pour éviter les doublons
    for article in articles:
        if article.find('h3', class_='major').text == subject:
            return

    # Trouver le bon emplacement pour insérer le nouvel article en fonction de l'ordre alphabétique
    position = None
    for index, article in enumerate(articles):
        current_subject = article.find('h3', class_='major').text
        if subject < current_subject:
            position = index
            break

    if position is None:
        articles[-1].insert_after(new_article)
    else:
        articles[position].insert_before(new_article)

    # Écrire le nouveau contenu dans le fichier
    with open(file_path, 'w') as file:
        file.write(str(soup))


# Création de la page html de la formation
def create_course_file(subject, description, training_plan, all_content, repo_path):
    # Configuration de Jinja2 pour utiliser le dossier courant comme source pour les templates
    env = Environment(loader=FileSystemLoader('.'))
    env.globals['extract_section_id'] = extract_section_id
    env.globals['quote'] = quote
    template = env.get_template('templates/course_template.html')

    # Remplir le template avec les données
    rendered_content = template.render(
        subject=subject,
        description=description,
        training_plan=training_plan,
        all_content=all_content
    )

    # Sauvegarder le contenu modifié dans un fichier HTML
    file_name = f"{subject.lower()}.html"
    course_dir = os.path.join(repo_path, 'AI-Learning', subject.lower())
    os.makedirs(course_dir, exist_ok=True)

    with open(os.path.join(course_dir, file_name), 'w') as file:
        file.write(rendered_content)

    return os.path.join(course_dir, file_name)


# Création des pages html pour chaque section de la formation
def create_section_file(subject, section_name, section_content, repo_path):
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('templates/section_template.html')

    # Encoder le sujet pour une utilisation dans les URL et les noms de fichier
    subject_lower_encoded = quote(subject.lower())

    section_id = extract_section_id(section_name)

    # Utiliser re pour extraire le numéro
    match = re.search(r'section(\d+)', section_id)
    if match:
        current_id = int(match.group(1))
        # Calculer les numéros des sections avant et après
        prev_id = current_id - 1
        next_id = current_id + 1
        # Générer les noms des sections
        prev_section = f'section{prev_id}'
        next_section = f'section{next_id}'

    if section_id == "section1":
        not_one = False
    else:
        not_one = True

    formatted_section_id = section_id.replace("section", "Section ")

    rendered_content = template.render(
        subject=subject,
        subject_lower_encoded=subject_lower_encoded,
        section_name=section_name,
        section_content=section_content,
        not_one=not_one,
        prev_section=prev_section,
        next_section=next_section,
        formatted_section_id=formatted_section_id
    )

    section_filename = f"{section_id}.html"
    course_dir = os.path.join(repo_path, 'AI-Learning',
                              subject.lower(), 'sections')
    os.makedirs(course_dir, exist_ok=True)

    with open(os.path.join(course_dir, section_filename), 'w') as file:
        file.write(rendered_content)

    return os.path.join(course_dir, section_filename)


# enkever le dernier boutton "Section suivante"
def remove_last_button(file_path):
    with open(file_path, 'r') as file:
        content = file.read()

    soup = BeautifulSoup(content, 'html.parser')

    # Trouver tous les boutons avec l'ID "last" et les supprimer
    buttons_to_remove = soup.find_all(id="last")

    for button in buttons_to_remove:
        button.extract()

    # Sauvegardez les modifications dans le fichier
    with open(file_path, 'w') as file:
        file.write(str(soup))


# Connexion au repo github et ajout de la formation
def handle_github(subject, description, training_plan, all_content):
    github_repo_url = 'https://github.com/Ziwo99/Ziwo99.github.io.git'

    with tempfile.TemporaryDirectory() as tmp_dir:
        # 1. Cloner le repo GitHub
        subprocess.run(['git', 'clone', github_repo_url, tmp_dir])

        # 2. Générer l'image pour le sujet
        generate_image(subject, tmp_dir)

        # 3. Ajouter l'article à courses.html
        courses_file_path = os.path.join(tmp_dir, 'courses.html')
        modify_html(courses_file_path, subject, description)

        # 4. Créer le fichier de cours en utilisant Jinja2
        create_course_file(subject, description,
                           training_plan, all_content, tmp_dir)

        # 5. Créer des fichiers pour chaque section
        last_section_name = None
        for section_name, _ in training_plan.items():
            section_content = all_content[section_name]
            match = re.search(r'<h1>.*?</h1>', section_content, re.DOTALL)
            modified_content = section_content.replace(match.group(0), '', 1)
            create_section_file(subject, section_name,
                                modified_content, tmp_dir)
            last_section_name = section_name

        # Calculer le chemin du dernier fichier de section
        last_section_id = extract_section_id(last_section_name)
        last_section_path = os.path.join(
            tmp_dir, 'AI-Learning', subject.lower(), 'sections', f"{last_section_id}.html")

        # Supprimer le bouton "Section suivante" du dernier fichier de section
        if last_section_path:
            remove_last_button(last_section_path)

        # 6. Pousser les modifications sur GitHub
        subprocess.run(['git', '-C', tmp_dir, 'add', '.'])
        subprocess.run(['git', '-C', tmp_dir, 'commit', '-m',
                       f'Ajout de la formation {subject}'])
        try:
            # Essayez de pousser les modifications
            subprocess.check_call(['git', '-C', tmp_dir, 'push'])
        except subprocess.CalledProcessError:
            # S'il y a une erreur (comme celle que vous avez vue), effectuez un pull
            subprocess.run(['git', '-C', tmp_dir, 'pull'])
            # Et essayez de pousser à nouveau
            subprocess.run(['git', '-C', tmp_dir, 'push'])
