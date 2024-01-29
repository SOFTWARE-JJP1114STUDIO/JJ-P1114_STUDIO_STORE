from flask import Flask, render_template, request, redirect, url_for, flash, make_response, session, abort, jsonify
import os
import xml.etree.ElementTree as ET
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = '@N9l9z8d1'  # Change this to a secure secret key

# Chemin vers le fichier XML des produits
products_xml_path = os.path.join('static', 'databases', 'products.xml')

# Chemin vers le fichier XML des utilisateurs
users_xml_path = os.path.join('static', 'databases', 'users.xml')

# Chemin vers le fichier XML des messages de contact
contact_messages_xml_path = os.path.join('static', 'databases', 'contact_messages.xml')

def parse_products():
    tree = ET.parse(products_xml_path)
    root = tree.getroot()
    products = []

    for product_elem in root.findall('product'):
        product = {
            'id': product_elem.find('id').text,
            'name': product_elem.find('name').text,
            'description': product_elem.find('description').text,
            'price': float(product_elem.find('price').text),
            'image': product_elem.find('image').text,
        }
        products.append(product)

    return products

def parse_users():
    tree = ET.parse(users_xml_path)
    root = tree.getroot()
    users = []

    for user_elem in root.findall('user'):
        user = {
            'id': user_elem.find('id').text,
            'username': user_elem.find('username').text,
            'password': user_elem.find('password').text,
            'email': user_elem.find('email').text,
        }
        users.append(user)

    return users

def save_user(user):
    tree = ET.parse(users_xml_path)
    root = tree.getroot()

    user_elem = ET.Element('user')
    for key, value in user.items():
        child_elem = ET.Element(key)
        child_elem.text = value
        user_elem.append(child_elem)

    root.append(user_elem)
    tree.write(users_xml_path)

@app.route('/')
def index():
    products = parse_products()
    special_offers = [
        {'title': 'Offre Spéciale 1', 'description': 'Réduction de 20% sur tous les produits cette semaine!'},
        {'title': 'Offre Spéciale 2', 'description': 'Achetez un produit, obtenez le deuxième à moitié prix!'},
        # Ajoutez d'autres offres spéciales selon votre choix
    ]
    current_year = 2024

    # Vérifiez si l'utilisateur est connecté en utilisant la session et/ou le cookie
    user_id = session.get('user_id') or request.cookies.get('user_id')

    # Si l'utilisateur n'a pas choisi de rester connecté, effacez la session s'il n'y a pas de cookie
    if not request.cookies.get('user_id') and 'user_id' in session:
        session.pop('user_id', None)

    return render_template('index.html', products=products, special_offers=special_offers, current_year=current_year, user_id=user_id)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # Hachez le mot de passe avant de le stocker
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        user = {
            'id': str(len(parse_users()) + 1),
            'username': username,
            'password': hashed_password,
            'email': email,
        }

        save_user(user)
        flash('Inscription réussie. Connectez-vous maintenant.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# ... (autres imports)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = request.form.get('remember')

        users = parse_users()
        user = next((u for u in users if u['username'] == username), None)

        if user and check_password_hash(user['password'], password):
            flash('Connexion réussie.', 'success')

            # Stockez l'ID de l'utilisateur dans la session
            session['user_id'] = user['id']

            # Si la case à cocher "Rester connecté" est cochée, définissez le cookie
            if remember:
                resp = make_response(redirect(url_for('index')))
                resp.set_cookie('user_id', user['id'])
                return resp

            return redirect(url_for('index'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect.', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    # Supprimez l'ID de l'utilisateur de la session
    session.pop('user_id', None)

    # Supprimez également l'ID de l'utilisateur du cookie
    resp = make_response(redirect(url_for('index')))
    resp.delete_cookie('user_id')

    flash('Vous avez été déconnecté.', 'success')
    return resp

@app.route('/account', methods=['GET', 'POST'])
def account():
    # Vérifiez si l'utilisateur est connecté en utilisant la session et/ou le cookie
    user_id = session.get('user_id') or request.cookies.get('user_id')

    # Si l'utilisateur n'est pas connecté, redirigez-le vers la page de connexion
    if not user_id:
        flash('Vous devez être connecté pour accéder à cette page.', 'error')
        return redirect(url_for('login'))

    # Obtenez les informations de l'utilisateur à partir de la base de données ou de la session, selon ce qui est disponible
    users = parse_users()
    user = next((u for u in users if u['id'] == user_id), None)

    if request.method == 'POST':
        # Mettez à jour les informations de l'utilisateur avec les nouvelles données du formulaire
        user['username'] = request.form['username']
        user['email'] = request.form['email']

        # Vérifiez si un nouveau mot de passe a été fourni et mettez à jour le mot de passe si nécessaire
        new_password = request.form['new_password']
        if new_password:
            # Hachez le nouveau mot de passe avant de le stocker
            hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
            user['password'] = hashed_password

        # Mettez à jour les informations dans la base de données
        update_user_in_database(user)

        flash('Informations mises à jour avec succès.', 'success')

    return render_template('account.html', user=user, user_id=user_id)

def update_user_in_database(user):
    # Ici, vous devez ajouter le code pour mettre à jour les informations de l'utilisateur dans votre base de données.
    # Cela dépendra de la manière dont vous avez implémenté votre gestion des utilisateurs et de la base de données.

    # Exemple : Mettez à jour la liste des utilisateurs avec les nouvelles informations
    users = parse_users()
    for idx, existing_user in enumerate(users):
        if existing_user['id'] == user['id']:
            users[idx] = user
            break

    # Enregistrez les modifications dans votre base de données (exemple avec XML)
    save_users_to_xml(users)

def save_users_to_xml(users):
    # Exemple : Enregistrez la liste des utilisateurs dans votre fichier XML
    root = ET.Element("users")
    for user in users:
        user_elem = ET.SubElement(root, "user")
        ET.SubElement(user_elem, "id").text = str(user['id'])
        ET.SubElement(user_elem, "username").text = user['username']
        ET.SubElement(user_elem, "email").text = user['email']
        ET.SubElement(user_elem, "password").text = user['password']

    tree = ET.ElementTree(root)
    tree.write("static/databases/users.xml")

def get_contact_messages():
    tree = ET.parse(contact_messages_xml_path)
    root = tree.getroot()
    messages = []

    for message_elem in root.findall('message'):
        id_elem = message_elem.find('id')
        id_value = id_elem.text if id_elem is not None else None

        message = {
            'id': id_value,
            'name': message_elem.find('name').text,
            'email': message_elem.find('email').text,
            'message': message_elem.find('message').text,
        }
        messages.append(message)

    return messages

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        access_code = request.form.get('access_code')

        # Vérifiez si le code d'accès correspond à celui des administrateurs
        if access_code == '@3d1f5-8mi-k80n-JJ-P1114':
            # Obtenez les messages de contact en utilisant la fonction get_contact_messages
            contact_messages = get_contact_messages()
            products = parse_products()  # Ajout pour récupérer les produits
            return render_template('admin.html', user_type='admin', contact_messages=contact_messages, products=products)

        # Vérifiez si le code d'accès correspond à celui du personnel
        elif access_code == 'S7t0r3-5t@ff-JJ-P1114':
            products = parse_products()  # Ajout pour récupérer les produits
            return render_template('staff.html', user_type='staff', products=products)

        else:
            flash('Code d\'accès incorrect.', 'error')

    return render_template('access_page.html', page_title='Admin/Staff Access', user_type=None)

def save_contact_message(message):
    tree = ET.parse(contact_messages_xml_path)
    root = tree.getroot()

    message_elem = ET.Element('message')
    for key, value in message.items():
        child_elem = ET.Element(key)
        child_elem.text = value
        message_elem.append(child_elem)

    root.append(message_elem)
    tree.write(contact_messages_xml_path)

@app.route('/admin/reply/<int:message_id>', methods=['GET', 'POST'])
def reply(message_id):
    # Logique pour afficher la page de réponse et gérer la réponse au message
    contact_messages = get_contact_messages()
    message = next((m for m in contact_messages if m['id'] == str(message_id)), None)

    if not message:
        abort(404)  # Arrêtez l'exécution si le message n'est pas trouvé

    if request.method == 'POST':
        reply_message = request.form['reply_message']

        # Logique pour envoyer la réponse (par exemple, l'enregistrement dans la base de données)
        send_reply(message_id, reply_message)

        flash('Réponse envoyée avec succès.', 'success')
        return redirect(url_for('admin'))

    return render_template('reply.html', message=message)

@app.route('/send_reply/<int:message_id>', methods=['POST'])
def send_reply(message_id):
    # Logique pour envoyer la réponse par e-mail
    reply_message = request.form['reply_message']

    # Récupérez les informations du message à partir de la base de données
    contact_messages = get_contact_messages()
    message = next((m for m in contact_messages if m['id'] == str(message_id)), None)

    if not message:
        abort(404)  # Arrêtez l'exécution si le message n'est pas trouvé

    # Adresse e-mail de l'expéditeur (votre adresse e-mail)
    sender_email = 'jj.p1114studio@gmail.com'

    # Adresse e-mail du destinataire (adresse e-mail de l'utilisateur)
    recipient_email = message['email']

    # Mot de passe de votre adresse e-mail (pour l'authentification SMTP)
    sender_password = 'wvdt ykml yeyd kaku'

    # Objet du message
    subject = 'Réponse à votre message'

    # Corps du message
    body = f"Bonjour {message['name']},\n\n{reply_message}"

    # Configuration du message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Configuration du serveur SMTP (pour Gmail dans cet exemple)
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587

    # Initialisez le serveur SMTP
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()

    # Connectez-vous au serveur SMTP avec votre adresse e-mail et votre mot de passe
    server.login(sender_email, sender_password)

    # Envoyez le message
    server.sendmail(sender_email, recipient_email, msg.as_string())

    # Fermez la connexion SMTP
    server.quit()

    flash('Réponse envoyée avec succès par e-mail.', 'success')
    return redirect(url_for('admin'))

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    # Vérifiez si l'utilisateur est connecté en utilisant la session et/ou le cookie
    user_id = session.get('user_id') or request.cookies.get('user_id')

    # Si l'utilisateur n'a pas choisi de rester connecté, effacez la session s'il n'y a pas de cookie
    if not request.cookies.get('user_id') and 'user_id' in session:
        session.pop('user_id', None)

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message_text = request.form['message']

        # Ajout de la génération de l'ID du message (par exemple, basé sur la longueur actuelle des messages)
        message_id = str(len(get_contact_messages()) + 1)

        message = {
            'id': message_id,
            'name': name,
            'email': email,
            'message': message_text,
        }

        # Enregistrez le message dans la base de données XML des messages de contact
        save_contact_message(message)

        flash('Votre message a été envoyé avec succès. Merci!', 'success')
        return redirect(url_for('contact'))

    return render_template('contact.html', user_id=user_id)

@app.route('/admin/delete_message/<int:message_id>', methods=['POST'])
def delete_message(message_id):
    # Logique pour supprimer le message (par exemple, à partir de la base de données)
    delete_contact_message(message_id)

    flash('Message supprimé avec succès.', 'success')
    return redirect(url_for('admin'))

def delete_contact_message(message_id):
    tree = ET.parse(contact_messages_xml_path)
    root = tree.getroot()

    for message_elem in root.findall('message'):
        if message_elem.find('id').text == str(message_id):
            root.remove(message_elem)
            break

    tree.write(contact_messages_xml_path)

def parse_products():
    tree = ET.parse(products_xml_path)
    root = tree.getroot()
    products = []

    for product_elem in root.findall('product'):
        product = {
            'id': product_elem.find('id').text,
            'name': product_elem.find('name').text,
            'description': product_elem.find('description').text,
            'price': float(product_elem.find('price').text),
            'image': product_elem.find('image').text,
        }
        products.append(product)

    return products

if __name__ == '__main__':
    app.run(debug=True)
