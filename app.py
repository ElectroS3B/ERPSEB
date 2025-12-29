import os
import pdfkit
from datetime import datetime
import qrcode
from fpdf import FPDF
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask import jsonify
from datetime import datetime, timedelta, time # Ajoutez 'time' ici
from flask import Flask, render_template, request, redirect, url_for, make_response
from flask import jsonify, request # Assurez-vous d'avoir bien importé ces deux-là
from flask import make_response







# --- 1. INITIALISATION DE L'APPLICATION ---
app = Flask(__name__)

# --- 2. CONFIGURATION ---
# Base de données
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'une_cle_secrete_aleatoire' # Nécessaire pour les messages flash
db = SQLAlchemy(app)

# Email (SMTP Gmail)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'commande.briffond@gmail.com'
app.config['MAIL_PASSWORD'] = 'cyvh blph wbzg mbnj' # Assurez-vous d'utiliser un mot de passe d'application

# --- 3. INITIALISATION DES EXTENSIONS ---

mail = Mail(app)

# --- 4. MODÈLES (TABLES) ---
class Societe(db.Model):
    __tablename__ = 'societe'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    adresse = db.Column(db.Text)
    code_postal = db.Column(db.String(10))
    ville = db.Column(db.String(100))
    coc_number = db.Column(db.String(50))
    logo_path = db.Column(db.String(255))

class Producteur(db.Model):
    __tablename__ = 'producteur'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    ggn = db.Column(db.String(50))

class Parcelle(db.Model):
    __tablename__ = 'parcelle'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    producteur_id = db.Column(db.Integer, db.ForeignKey('producteur.id'), nullable=False)
    ggn = db.Column(db.String(50))
    producteur_rel = db.relationship('Producteur', backref='parcelles')

class TypeProduit(db.Model):
    __tablename__ = 'type_produit'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)

class Variete(db.Model):
    __tablename__ = 'variete'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)
    type_produit_id = db.Column(db.Integer, db.ForeignKey('type_produit.id'))
    type_parent = db.relationship('TypeProduit', backref='varietes')

class Calibre(db.Model):
    __tablename__ = 'calibre'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(20), nullable=False)

class TypeConditionnement(db.Model):
    __tablename__ = 'type_conditionnement'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50))
    poids_unite = db.Column(db.Float)

class ProduitFini(db.Model):
    __tablename__ = 'produit_fini'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    type_id = db.Column(db.Integer, db.ForeignKey('type_produit.id'))
    variete_id = db.Column(db.Integer, db.ForeignKey('variete.id'))
    calibre_id = db.Column(db.Integer, db.ForeignKey('calibre.id'))
    parcelle_id = db.Column(db.Integer, db.ForeignKey('parcelle.id'))
    cond_id = db.Column(db.Integer, db.ForeignKey('type_conditionnement.id'))
    nb_unites = db.Column(db.Integer)
    poids_unite_reel = db.Column(db.Float)
    poids_total = db.Column(db.Float)
    statut = db.Column(db.String(20), default='STOCK') 
    date_statut = db.Column(db.DateTime)
    date_creation = db.Column(db.DateTime, default=datetime.now)

    # Relations techniques (Stock)
    type_rel = db.relationship('TypeProduit')
    variete_rel = db.relationship('Variete')
    calibre_rel = db.relationship('Calibre')
    parcelle_rel = db.relationship('Parcelle')
    cond_rel = db.relationship('TypeConditionnement')
    
    # ON NE MET RIEN ICI POUR LES LIVRAISONS : 
    # Le lien sera créé automatiquement par le 'backref' de DetailLivraison

class Client(db.Model):
    __tablename__ = 'client'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    adresse = db.Column(db.Text)
    ville = db.Column(db.String(100))
    code_postal = db.Column(db.String(20))
    telephone = db.Column(db.String(20))
    email = db.Column(db.String(120))  # Email principal
    email2 = db.Column(db.String(120)) # Deuxième email
    email3 = db.Column(db.String(120)) # Troisième email
    ggn_client = db.Column(db.String(50))

class TarifClient(db.Model):
    __tablename__ = 'tarif_client'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    
    # On utilise les noms exacts des tables pour les Foreign Keys
    type_id = db.Column(db.Integer, db.ForeignKey('type_produit.id'))
    variete_id = db.Column(db.Integer, db.ForeignKey('variete.id'))
    calibre_id = db.Column(db.Integer, db.ForeignKey('calibre.id'))
    
    # CORRECTION ICI : le nom de la table est 'type_conditionnement'
    cond_id = db.Column(db.Integer, db.ForeignKey('type_conditionnement.id')) 
    
    prix_ht = db.Column(db.Float, nullable=False, default=0.0)

    # Relations pour faciliter l'affichage plus tard
    client = db.relationship('Client', backref='tarifs')
    type_rel = db.relationship('TypeProduit')
    variete_rel = db.relationship('Variete')
    calibre_rel = db.relationship('Calibre')
    cond_rel = db.relationship('TypeConditionnement')


class Transporteur(db.Model):
    __tablename__ = 'transporteur'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    telephone = db.Column(db.String(20))
    email = db.Column(db.String(100))

class Commande(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero_commande = db.Column(db.String(20), unique=True, nullable=False)
    date_creation = db.Column(db.DateTime, default=datetime.now)
    date_livraison_souhaitee = db.Column(db.Date, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    transporteur_id = db.Column(db.Integer, db.ForeignKey('transporteur.id'))
    observations = db.Column(db.Text)
    statut = db.Column(db.String(20), default="En attente") # En attente, Expédiée, Annulée

    # Relations
    client_rel = db.relationship('Client', backref='commandes')
    transporteur_rel = db.relationship('Transporteur', backref='commandes')
    lignes = db.relationship('LigneCommande', backref='commande', cascade="all, delete-orphan")

class LigneCommande(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    commande_id = db.Column(db.Integer, db.ForeignKey('commande.id'), nullable=False)
    type_produit_id = db.Column(db.Integer, db.ForeignKey('type_produit.id'))
    variete_id = db.Column(db.Integer, db.ForeignKey('variete.id'))
    calibre_id = db.Column(db.Integer, db.ForeignKey('calibre.id'))
    conditionnement_id = db.Column(db.Integer, db.ForeignKey('type_conditionnement.id'))
    quantite = db.Column(db.Float, nullable=False) # Nombre ou Poids

    # Relations pour l'affichage
    type_rel = db.relationship('TypeProduit')
    variete_rel = db.relationship('Variete')
    calibre_rel = db.relationship('Calibre')
    cond_rel = db.relationship('TypeConditionnement')



class Livraison(db.Model):
    __tablename__ = 'livraison'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    date_livraison = db.Column(db.DateTime, default=datetime.now)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    transporteur_id = db.Column(db.Integer, db.ForeignKey('transporteur.id')) 
    numero_bl = db.Column(db.String(20), unique=True)
    observations = db.Column(db.Text)  # Champ pour le texte libre sur le BL
    numero_facture = db.Column(db.String(50), nullable=True)

    

    client_rel = db.relationship('Client', backref='livraisons')
    transporteur_rel = db.relationship('Transporteur', backref='livraisons')
    details = db.relationship('DetailLivraison', backref='livraison_parente', cascade="all, delete-orphan")

class DetailLivraison(db.Model):
    __tablename__ = 'detail_livraison'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    livraison_id = db.Column(db.Integer, db.ForeignKey('livraison.id'), nullable=False)
    produit_id = db.Column(db.Integer, db.ForeignKey('produit_fini.id'), nullable=False)
    prix_unitaire_ht = db.Column(db.Float)

    # UNE SEULE RELATION VERS LE PRODUIT AVEC BACKREF
    # Cela crée la propriété 'historique_livraisons' utilisable dans le produit
    produit_rel = db.relationship('ProduitFini', backref=db.backref('historique_livraisons', lazy=True))
    
    # RELATION VERS LA LIVRAISON (pour remonter au client)
    livraison_rel = db.relationship('Livraison', backref=db.backref('details_items', lazy=True))

# --- 5. LOGIQUE PDF ---
def generer_pdf_bl(livraison):
    ma_societe = Societe.query.first()
    nom_soc = ma_societe.nom if ma_societe else "MA SOCIÉTÉ"
    coc_soc = ma_societe.coc_number if ma_societe else "CoC non renseigné"
    adr_soc = f"{ma_societe.adresse}, {ma_societe.code_postal} {ma_societe.ville}" if ma_societe else ""

    if not os.path.exists('static/bl'):
        os.makedirs('static/bl')

    pdf = FPDF('L', 'mm', 'A4')
    pdf.add_page()
    
    # --- EN-TÊTE ---
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(140, 10, nom_soc.upper(), ln=0)
    pdf.set_font("Arial", '', 10)
    
    # Date et Numéro de BL (Sécurisé)
    date_str = livraison.date_livraison.strftime('%d/%m/%Y') if livraison.date_livraison else "N/A"
    num_bl = livraison.numero_bl if livraison.numero_bl else f"TEMP_{livraison.id}"
    
    pdf.cell(137, 10, f"Date: {date_str}", ln=1, align='R')
    pdf.cell(140, 5, adr_soc, ln=0)
    pdf.cell(137, 5, f"BL N°: {num_bl}", ln=1, align='R')
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(140, 5, f"CoC: {coc_soc}", ln=1)
    pdf.ln(8)

    # --- CLIENT & LOGISTIQUE ---
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(138, 7, "CLIENT", border=1, ln=0, fill=True)
    pdf.cell(139, 7, "LOGISTIQUE", border=1, ln=1, fill=True)
    pdf.set_font("Arial", '', 9)
    y_start = pdf.get_y()
    
    client_info = f"{livraison.client_rel.nom}\n{livraison.client_rel.adresse}\n{livraison.client_rel.code_postal} {livraison.client_rel.ville}"
    pdf.multi_cell(138, 5, client_info, border=1)
    y_end_client = pdf.get_y()
    
    pdf.set_xy(148, y_start)
    if livraison.transporteur_rel:
        nom_t = livraison.transporteur_rel.nom
        tel_t = getattr(livraison.transporteur_rel, 'telephone', "N/A")
        mail_t = getattr(livraison.transporteur_rel, 'email', "N/A")
        transp_info = f"Transporteur: {nom_t}\nTel: {tel_t or 'N/A'}\nEmail: {mail_t or 'N/A'}"
    else:
        transp_info = "Transporteur: Non spécifié"

    pdf.multi_cell(139, 5, transp_info, border=1)
    pdf.set_y(max(y_end_client, pdf.get_y()) + 8)

    # --- TABLEAU DES PRODUITS ---
    w_lot, w_var, w_cal, w_parc, w_ggn, w_cond = 12, 40, 20, 30, 30, 35
    w_nb, w_pds, w_pu, w_pt = 15, 25, 35, 35

    pdf.set_font("Arial", 'B', 8)
    pdf.set_fill_color(220, 220, 220)
    cols = [("Lot", w_lot), ("Variété", w_var), ("Cal.", w_cal), ("Parcelle", w_parc), 
            ("GGN", w_ggn), ("Cond.", w_cond), ("Colis", w_nb), ("Poids kg", w_pds), ("Prix HT", w_pu), ("Total HT", w_pt)]
    
    for label, width in cols:
        pdf.cell(width, 8, label, border=1, align='C', fill=True)
    pdf.ln(8)

    # Tri sécurisé
    details_tries = sorted(livraison.details, key=lambda d: (
        d.produit_rel.type_rel.nom if d.produit_rel.type_rel else "", 
        d.produit_rel.calibre_rel.nom if d.produit_rel.calibre_rel else ""
    ))

    pdf.set_font("Arial", '', 8)
    total_poids = total_unites = total_ht = 0
    sub_poids = sub_unites = sub_ht = 0
    last_group = None

    for d in details_tries:
        p = d.produit_rel
        type_nom = p.type_rel.nom if p.type_rel else "Inconnu"
        cal_nom = p.calibre_rel.nom if p.calibre_rel else "N/A"
        current_group = f"{type_nom} - {cal_nom}"

        # Gestion des sous-totaux
        if last_group and current_group != last_group:
            pdf.set_font("Arial", 'BI', 8)
            pdf.set_fill_color(245, 245, 245)
            w_label_sub = w_lot + w_var + w_cal + w_parc + w_ggn + w_cond
            pdf.cell(w_label_sub, 7, f"Sous-total {last_group} :", border=1, align='R', fill=True)
            pdf.cell(w_nb, 7, f"{sub_unites}", border=1, align='C', fill=True)
            pdf.cell(w_pds, 7, f"{round(sub_poids, 2)}", border=1, align='R', fill=True)
            pdf.cell(w_pu + w_pt, 7, f"{format(sub_ht, '.2f')} EUR HT", border=1, ln=1, align='R', fill=True)
            pdf.set_font("Arial", '', 8)
            sub_poids = sub_unites = sub_ht = 0

        # Données de la ligne (SÉCURISÉES AVEC "OR 0" OU "OR 0.0")
        poids_ligne = p.poids_total or 0.0
        nb_u_ligne = p.nb_unites or 0
        pu_ht = d.prix_unitaire_ht or 0.0
        montant_ligne = poids_ligne * pu_ht

        ggn_final = "N/A"
        if p.parcelle_rel:
            ggn_final = p.parcelle_rel.ggn or (p.parcelle_rel.producteur_rel.ggn if p.parcelle_rel.producteur_rel else "N/A")

        pdf.cell(w_lot, 7, f"#{p.id}", border=1, align='C')
        var_nom = p.variete_rel.nom if p.variete_rel else "N/A"
        pdf.cell(w_var, 7, f" {type_nom} ({var_nom})", border=1)
        pdf.cell(w_cal, 7, f" {cal_nom}", border=1, align='C')
        pdf.cell(w_parc, 7, f" {p.parcelle_rel.nom if p.parcelle_rel else 'N/A'}", border=1)
        pdf.cell(w_ggn, 7, f" {ggn_final}", border=1, align='C')
        pdf.cell(w_cond, 7, f" {p.cond_rel.nom if p.cond_rel else 'N/A'}", border=1, align='C')
        pdf.cell(w_nb, 7, f"{nb_u_ligne}", border=1, align='C')
        pdf.cell(w_pds, 7, f"{round(poids_ligne, 2)}", border=1, align='R')
        pdf.cell(w_pu, 7, f"{format(pu_ht, '.3f')} EUR", border=1, align='R')
        pdf.cell(w_pt, 7, f"{format(montant_ligne, '.2f')} EUR", border=1, ln=1, align='R')

        sub_poids += poids_ligne
        sub_unites += nb_u_ligne
        sub_ht += montant_ligne
        
        total_poids += poids_ligne
        total_unites += nb_u_ligne
        total_ht += montant_ligne
        last_group = current_group

    # Dernier sous-total
    if last_group:
        pdf.set_font("Arial", 'BI', 8)
        pdf.set_fill_color(245, 245, 245)
        w_label_sub = w_lot + w_var + w_cal + w_parc + w_ggn + w_cond
        pdf.cell(w_label_sub, 7, f"Sous-total {last_group} :", border=1, align='R', fill=True)
        pdf.cell(w_nb, 7, f"{sub_unites}", border=1, align='C', fill=True)
        pdf.cell(w_pds, 7, f"{round(sub_poids, 2)}", border=1, align='R', fill=True)
        pdf.cell(w_pu + w_pt, 7, f"{format(sub_ht, '.2f')} EUR HT", border=1, ln=1, align='R', fill=True)

    # --- TOTAL GÉNÉRAL ---
# --- TOTAL GÉNÉRAL ---
    pdf.ln(4)
    
    # Calcul du nombre de lots
    nb_lots = len(livraison.details)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(40, 40, 40)
    pdf.set_text_color(255, 255, 255)
    
    # Largeur combinée pour l'étiquette (on inclut le nombre de lots ici)
    w_label_total = w_lot + w_var + w_cal + w_parc + w_ggn + w_cond
    
    # Texte du label avec le nombre de lots
    label_text = f"TOTAL ({nb_lots} LOTS) : "
    
    pdf.cell(w_label_total, 10, label_text, border=1, fill=True, align='R')
    pdf.cell(w_nb, 10, f"{total_unites}", border=1, fill=True, align='C')
    pdf.cell(w_pds, 10, f"{round(total_poids, 2)} kg", border=1, fill=True, align='R')
    pdf.cell(w_pu + w_pt, 10, f"{format(total_ht, '.2f')} EUR HT", border=1, fill=True, ln=1, align='R')
    
    # Remettre la couleur du texte en noir pour la suite si besoin
    pdf.set_text_color(0, 0, 0)


    # Affichage des observations en bas du document
    if livraison.observations and livraison.observations.strip():
        pdf.ln(10) # Espacement avant le bloc
        pdf.set_font("Arial", 'B', 10)
        pdf.set_fill_color(230, 230, 230) # Gris très clair pour le titre
        pdf.cell(0, 8, " OBSERVATIONS / INSTRUCTIONS DE LIVRAISON :", ln=1, fill=True)
        
        pdf.set_font("Arial", '', 10)
        # On utilise multi_cell pour que le texte revienne à la ligne tout seul
        # border=1 dessine un cadre autour du texte
        pdf.multi_cell(0, 6, str(livraison.observations), border=1, align='L')  




    nom_fichier = f"static/bl/BL_{livraison.id}.pdf"
    pdf.output(nom_fichier)
    return nom_fichier






@app.route('/envoyer_bl/<int:id>')
def envoyer_bl(id):
    livraison = Livraison.query.get_or_404(id)
    client = livraison.client_rel
    
    if not client:
        return "Erreur : Aucun client associé à cette livraison.", 400

    # 1. On définit les destinataires (les 3 emails s'ils existent)
    destinataires = [e for e in [client.email, client.email2, client.email3] if e and e.strip()]

    if not destinataires:
        return "Erreur : Aucune adresse email renseignée pour ce client.", 400

    # 2. CRUCIAL : On génère le PDF ici et on stocke son nom dans pdf_path
    # Assurez-vous que le nom de votre fonction est bien generer_pdf_bl
    pdf_path = generer_pdf_bl(livraison) 

    # 3. On prépare le message unique
    msg = Message(
        f"Bon de Livraison n°{livraison.numero_bl}",
        sender=app.config['MAIL_USERNAME'],
        recipients=destinataires
    )
    msg.body = f"Bonjour,\n\nVeuillez trouver ci-joint le bon de livraison n°{livraison.numero_bl}."
    
    # 4. On attache le fichier généré
    try:
        with app.open_resource(pdf_path) as fp:
            msg.attach(f"BL_{livraison.numero_bl}.pdf", "application/pdf", fp.read())
        
        mail.send(msg)
        return render_template('success_mail.html')
        
    except Exception as e:
        return f"Erreur lors de l'envoi ou de la génération : {str(e)}", 500









# --- FONCTIONS ---

def generer_prochain_numero_bl():
    annee_actuelle = datetime.now().year
    prefixe = f"{annee_actuelle}-"
    
    # On cherche le dernier BL de l'année en cours
    dernier_bl = Livraison.query.filter(Livraison.numero_bl.like(f"{prefixe}%"))\
                                .order_by(Livraison.id.desc()).first()
    
    if dernier_bl and dernier_bl.numero_bl:
        try:
            # On récupère le dernier numéro après le tiret et on ajoute 1
            dernier_index = int(dernier_bl.numero_bl.split('-')[1])
            nouveau_numero = dernier_index + 1
        except (IndexError, ValueError):
            nouveau_numero = 1
    else:
        nouveau_numero = 1
        
    return f"{prefixe}{str(nouveau_numero).zfill(3)}" # Donne 2025-001







def generer_numero_commande():
    annee = datetime.now().year
    prefixe = f"CM-{annee}-"
    derniere_commande = Commande.query.filter(Commande.numero_commande.like(f"{prefixe}%")).order_by(Commande.id.desc()).first()
    
    if derniere_commande:
        dernier_num = int(derniere_commande.numero_commande.split('-')[-1])
        nouveau_num = dernier_num + 1
    else:
        nouveau_num = 1
        
    return f"{prefixe}{nouveau_num:03d}"



def generer_etiquettes_multiples(produit):
    pdf = FPDF(format=(100, 150))
    
    # Récupération des infos de la société (la première ligne de la table)
    infos_societe = Societe.query.first()
    nom_soc = infos_societe.nom if infos_societe else "Ma Société"
    adr_soc = infos_societe.adresse if infos_societe else ""
    coc_soc = infos_societe.coc_number if infos_societe else ""

    # Données du QR Code
    qr_content = f"LOT:{produit.id} | VAR:{produit.variete_rel.nom} | POIDS:{produit.poids_unite_reel}kg"
    
    # Création de l'image du QR Code
    qr = qrcode.make(qr_content)
    qr_filename = f"static/etiquettes/qr_temp_{produit.id}.png"
    qr.save(qr_filename)

    for i in range(1, produit.nb_unites + 1):
        pdf.add_page()
        
        # --- EN-TÊTE SOCIÉTÉ ---
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 5, nom_soc.upper(), ln=True, align='L')
        pdf.set_font("Arial", '', 8)
        pdf.cell(0, 4, adr_soc, ln=True, align='L')
        if coc_soc:
            pdf.cell(0, 4, f"CoC: {coc_soc}", ln=True, align='L')
        
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 90, pdf.get_y()) # Petite ligne de séparation
        pdf.ln(5)

        # --- INFOS PRODUIT ---
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "ETIQUETTE PRODUIT", ln=True, align='C')
        pdf.ln(3)
        
        pdf.set_font("Arial", '', 11)
        pdf.cell(0, 7, f"Date: {produit.date_creation.strftime('%d/%m/%Y')}", ln=True)
        pdf.cell(0, 7, f"Lot: {produit.id} | Unite: {i}/{produit.nb_unites}", ln=True)
        
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, f"{produit.type_rel.nom} - {produit.variete_rel.nom}", ln=True)
        pdf.cell(0, 10, f"CALIBRE: {produit.calibre_rel.nom}", ln=True)
        
        pdf.set_font("Arial", '', 11)
        pdf.cell(0, 7, f"Origine: {produit.parcelle_rel.nom}", ln=True)
        pdf.cell(0, 7, f"Producteur GGN: {produit.parcelle_rel.producteur_rel.ggn}", ln=True)
        
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, f"POIDS NET: {produit.poids_unite_reel} kg", ln=True)
        pdf.cell(0, 8, f"Type: {produit.cond_rel.nom}", ln=True)
        
        # Insertion du QR Code
        pdf.image(qr_filename, x=65, y=110, w=30)

    if not os.path.exists('static/etiquettes'): os.makedirs('etiquettes')
    pdf.output(f"static/etiquettes/etiquette_{produit.id}.pdf")
    
    if os.path.exists(qr_filename):
        os.remove(qr_filename)

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('base.html')




@app.route('/commande/pdf/<int:id>')
def generer_pdf_commande(id):
    commande = Commande.query.get_or_404(id)
    
    # 1. Préparer le contenu
    html = render_template('pdf_commande.html', commande=commande, now=datetime.now())
    
    # 2. CONFIGURATION WINDOWS (Le chemin vers l'exécutable)
    # Vérifiez bien que ce chemin est correct sur votre disque C:
    path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    
    # 3. Options
    options = {
        'page-size': 'A4',
        'encoding': "UTF-8",
        'no-outline': None
    }
    
    try:
        # On ajoute "configuration=config" ici
        pdf = pdfkit.from_string(html, False, options=options, configuration=config)
        
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=Commande_{commande.numero_commande}.pdf'
        return response
        
    except Exception as e:
        return f"Erreur lors de la génération du PDF : {str(e)}"

from flask import jsonify, request

@app.route('/api/get_prix_client')
def api_get_prix_client():
    # 1. Récupération des paramètres envoyés par le JavaScript (?client_id=X&produit_id=Y)
    client_id = request.args.get('client_id')
    produit_id = request.args.get('produit_id')
    
    # Sécurité : si on n'a pas les infos, on renvoie 0
    if not client_id or not produit_id:
        return jsonify({'prix': 0.0})

    # 2. On récupère le produit pour connaître ses caractéristiques (variété, calibre, etc.)
    # Attention : vérifiez si votre classe est 'ProduitFini' ou 'Produit'
    produit = ProduitFini.query.get(produit_id)
    if not produit:
        return jsonify({'prix': 0.0})

    # 3. On cherche dans la table TarifClient si une règle de prix correspond
    # On compare le Client ET toute la combinaison de l'article
    tarif = TarifClient.query.filter_by(
        client_id=client_id,
        type_id=produit.type_id,
        variete_id=produit.variete_id,
        calibre_id=produit.calibre_id,
        cond_id=produit.cond_id # Ou type_conditionnement_id selon votre modèle
    ).first()

    # 4. On renvoie la réponse au format JSON (compréhensible par le JavaScript)
    if tarif:
        return jsonify({'prix': tarif.prix_ht})
    
    # Si aucun tarif n'est trouvé en base, on renvoie 0.0
    return jsonify({'prix': 0.0})

@app.route('/nouvelle_commande', methods=['GET', 'POST'])
def nouvelle_commande():
    if request.method == 'POST':
        try:
            # 1. Création de l'en-tête de commande
            date_liv_str = request.form.get('date_livraison')
            nouvelle_cmd = Commande(
                numero_commande = generer_numero_commande(),
                date_livraison_souhaitee = datetime.strptime(date_liv_str, '%Y-%m-%d').date(),
                client_id = int(request.form.get('client_id')),
                transporteur_id = int(request.form.get('transporteur_id')) if request.form.get('transporteur_id') else None,
                observations = request.form.get('observations'),
                statut = "En attente"
            )
            db.session.add(nouvelle_cmd)
            db.session.flush() # Récupère l'ID pour les lignes

            # 2. Récupération des listes dynamiques
            types = request.form.getlist('type_produit_id[]')
            varietes = request.form.getlist('variete_id[]')
            calibres = request.form.getlist('calibre_id[]')
            conds = request.form.getlist('conditionnement_id[]')
            quantites = request.form.getlist('quantite[]')

            # 3. Création des lignes
            for i in range(len(types)):
                if quantites[i]: # On vérifie qu'une quantité est saisie
                    ligne = LigneCommande(
                        commande_id = nouvelle_cmd.id,
                        type_produit_id = int(types[i]),
                        variete_id = int(varietes[i]) if varietes[i] else None,
                        calibre_id = int(calibres[i]) if calibres[i] else None,
                        conditionnement_id = int(conds[i]) if conds[i] else None,
                        quantite = float(quantites[i])
                    )
                    db.session.add(ligne)

            db.session.commit()
            return redirect(url_for('historique_commandes'))

        except Exception as e:
            db.session.rollback()
            print(f"Erreur enregistrement commande : {e}")
            # Optionnel : ajouter un message flash ici

    # Données pour le chargement de la page (GET)
    return render_template('nouvelle_commande.html', 
                           prochain_numero=generer_numero_commande(),
                           clients=Client.query.all(), 
                           transporteurs=Transporteur.query.all(),
                           types=TypeProduit.query.all(),
                           varietes=Variete.query.all(),
                           calibres=Calibre.query.all(),
                           conditionnements=TypeConditionnement.query.all())


@app.route('/historique_commandes')
def historique_commandes():
    # 1. Récupération des filtres depuis l'URL
    f_client = request.args.get('client_id')
    f_statut = request.args.get('statut')
    f_debut = request.args.get('date_debut')
    f_fin = request.args.get('date_fin')

    # 2. Logique des dates par défaut si non saisies
    aujourdhui = datetime.now().date()
    if not f_debut:
        f_debut = (aujourdhui - timedelta(days=7)).strftime('%Y-%m-%d')
    if not f_fin:
        f_fin = (aujourdhui + timedelta(days=30)).strftime('%Y-%m-%d')

    # 3. Requête de base
    query = Commande.query

    # 4. Application des filtres
    if f_client:
        query = query.filter(Commande.client_id == f_client)
    if f_statut:
        query = query.filter(Commande.statut == f_statut)
    
    # Filtrage par dates (on convertit les chaînes f_debut/f_fin en objets date pour SQLAlchemy)
    if f_debut:
        date_obj_debut = datetime.strptime(f_debut, '%Y-%m-%d').date()
        query = query.filter(Commande.date_livraison_souhaitee >= date_obj_debut)
    if f_fin:
        date_obj_fin = datetime.strptime(f_fin, '%Y-%m-%d').date()
        query = query.filter(Commande.date_livraison_souhaitee <= date_obj_fin)

    # 5. Tri et exécution
    # Conseil : Trié par date de livraison souhaitée pour voir les échéances proches
    commandes = query.order_by(Commande.date_livraison_souhaitee.asc()).all()
    
    clients = Client.query.all()
    
    return render_template('historique_commandes.html', 
                           commandes=commandes, 
                           clients=clients,
                           f_client=f_client, 
                           f_statut=f_statut, 
                           f_debut=f_debut, 
                           f_fin=f_fin)



from flask import make_response
from fpdf import FPDF
from datetime import datetime

@app.route('/imprimer_recap_commandes')
def imprimer_recap_commandes():
    # 1. Récupération des filtres depuis l'URL
    client_id = request.args.get('client_id')
    statut = request.args.get('statut')
    date_debut = request.args.get('date_debut')
    date_fin = request.args.get('date_fin')

    # 2. INITIALISATION DE LA VARIABLE QUERY (C'est ce qui manquait !)
    query = Commande.query
    
    if client_id and client_id != "":
        query = query.filter(Commande.client_id == client_id)
    if statut and statut != "":
        query = query.filter(Commande.statut == statut)
    if date_debut and date_debut != "":
        query = query.filter(Commande.date_livraison_souhaitee >= datetime.strptime(date_debut, '%Y-%m-%d'))
    if date_fin and date_fin != "":
        query = query.filter(Commande.date_livraison_souhaitee <= datetime.strptime(date_fin, '%Y-%m-%d'))
    
    # Maintenant 'query' existe et on peut appliquer le tri
    commandes = query.order_by(Commande.date_livraison_souhaitee.asc()).all()

    # 3. Création du PDF
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    
    # --- STYLE & TITRE ---
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(277, 10, "RECAPITULATIF DES PREPARATIONS", ln=True, align='C')
    pdf.ln(5)

# --- EN-TETE DU TABLEAU (Largeurs ajustées) ---
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(50, 50, 50) 
    pdf.set_text_color(255, 255, 255)
    
    # Nouvelles largeurs : Date(25) + Cmd(30) + Client(45) + Produit(60) + Variete(35) + Calibre(25) + Qte(20) + Unite(37) = 277mm
    pdf.cell(25, 8, "Date Liv.", 1, 0, 'C', True)
    pdf.cell(30, 8, "N* Cmd", 1, 0, 'C', True) # Élargie
    pdf.cell(45, 8, "Client", 1, 0, 'C', True)
    pdf.cell(60, 8, "Produit", 1, 0, 'C', True)
    pdf.cell(35, 8, "Variete", 1, 0, 'C', True)
    pdf.cell(25, 8, "Calibre", 1, 0, 'C', True)
    pdf.cell(20, 8, "Qte", 1, 0, 'C', True)
    pdf.cell(37, 8, "Unite", 1, 1, 'C', True) # Rétrécie

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", '', 10)
    
    totaux_produits = {}
    derniere_cmd_id = None

    # 4. BOUCLE SUR LES COMMANDES (Appliquer les mêmes largeurs ici)
    for cmd in commandes:
        if derniere_cmd_id is not None and derniere_cmd_id != cmd.id:
            pdf.set_fill_color(230, 230, 230)
            pdf.cell(277, 5, "", 1, 1, 'C', True)
        
        derniere_cmd_id = cmd.id

        for ligne in cmd.lignes:
            nom_prod = ligne.type_rel.nom
            nom_var = ligne.variete_rel.nom if ligne.variete_rel else "-"
            nom_cal = ligne.calibre_rel.nom if ligne.calibre_rel else "-"
            nom_cond = ligne.cond_rel.nom if ligne.cond_rel else "unites"
            
            pdf.cell(25, 8, cmd.date_livraison_souhaitee.strftime('%d/%m/%Y'), 1)
            pdf.cell(30, 8, str(cmd.numero_commande), 1, 0, 'C') # Largeur 30
            pdf.cell(45, 8, cmd.client_rel.nom[:22], 1)
            pdf.cell(60, 8, nom_prod, 1)
            pdf.cell(35, 8, nom_var, 1)
            pdf.cell(25, 8, nom_cal, 1, 0, 'C')
            pdf.cell(20, 8, str(ligne.quantite), 1, 0, 'C')
            pdf.cell(37, 8, nom_cond, 1, 1) # Largeur 37

            # Stockage pour le résumé regroupé
            cle_total = (nom_prod, f"{nom_var} | Calibre: {nom_cal} ({nom_cond})")
            totaux_produits[cle_total] = totaux_produits.get(cle_total, 0) + ligne.quantite

    # 5. PAGE DE RÉSUMÉ REGROUPÉ
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(277, 10, "TOTAL GENERAL A PREPARER (REGROUPE PAR TYPE)", ln=True)
    pdf.ln(5)
    
    produits_tries = sorted(totaux_produits.items(), key=lambda x: x[0][0])

    dernier_type = None
    for (type_p, details), total in produits_tries:
        if type_p != dernier_type:
            pdf.ln(2)
            pdf.set_font("Arial", 'B', 11)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(277, 8, f" TYPE : {type_p.upper()}", 1, 1, 'L', True)
            dernier_type = type_p
        
        pdf.set_font("Arial", '', 11)
        pdf.cell(15, 10, "", 0, 0) # Marge
        pdf.cell(180, 10, details, 1)
        pdf.cell(40, 10, f"{total}", 1, 1, 'C')

    # Génération de la réponse
    response = make_response(pdf.output(dest='S').encode('latin-1'))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=recap_commandes.pdf'
    return response



@app.route('/supprimer_commande/<int:id>')
def supprimer_commande(id):
    commande = Commande.query.get_or_404(id)
    try:
        db.session.delete(commande)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Erreur suppression : {e}")
    return redirect(url_for('historique_commandes'))

@app.route('/modifier_commande/<int:id>', methods=['GET', 'POST'])
def modifier_commande(id):
    commande = Commande.query.get_or_404(id)
    if request.method == 'POST':
        try:
            # Mise à jour de l'en-tête
            commande.date_livraison_souhaitee = datetime.strptime(request.form.get('date_livraison'), '%Y-%m-%d').date()
            commande.client_id = int(request.form.get('client_id'))
            commande.transporteur_id = int(request.form.get('transporteur_id')) if request.form.get('transporteur_id') else None
            commande.observations = request.form.get('observations')
            commande.statut = request.form.get('statut')

            # Pour simplifier la modification des lignes : on supprime les anciennes et on recrée les nouvelles
            LigneCommande.query.filter_by(commande_id=commande.id).delete()
            
            types = request.form.getlist('type_produit_id[]')
            varietes = request.form.getlist('variete_id[]')
            calibres = request.form.getlist('calibre_id[]')
            conds = request.form.getlist('conditionnement_id[]')
            quantites = request.form.getlist('quantite[]')

            for i in range(len(types)):
                if quantites[i]:
                    ligne = LigneCommande(
                        commande_id=commande.id,
                        type_produit_id=int(types[i]),
                        variete_id=int(varietes[i]) if varietes[i] else None,
                        calibre_id=int(calibres[i]) if calibres[i] else None,
                        conditionnement_id=int(conds[i]) if conds[i] else None,
                        quantite=float(quantites[i])
                    )
                    db.session.add(ligne)

            db.session.commit()
            return redirect(url_for('historique_commandes'))
        except Exception as e:
            db.session.rollback()
            print(f"Erreur modification : {e}")

    # Données pour charger le formulaire de modification
    return render_template('modifier_commande.html', 
                           commande=commande,
                           clients=Client.query.all(),
                           transporteurs=Transporteur.query.all(),
                           types=TypeProduit.query.all(),
                           varietes=Variete.query.all(),
                           calibres=Calibre.query.all(),
                           conditionnements=TypeConditionnement.query.all())
@app.route('/stock')
def stock():
    # On récupère tous les produits qui ont le statut EN_STOCK
    produits_en_stock = ProduitFini.query.filter_by(statut='EN_STOCK').all()
    return render_template('stock.html', produits=produits_en_stock)


@app.route('/reparer_stock')
def reparer_stock():
    # On passe tous les produits qui ne sont pas expédiés en statut 'EN_STOCK'
    produits = ProduitFini.query.filter(ProduitFini.statut != 'EXPEDIE').all()
    for p in produits:
        p.statut = 'EN_STOCK'
    db.session.commit()
    return "Stock réparé ! Tous les produits sont maintenant en statut 'EN_STOCK'."

@app.route('/sortir_du_stock/<int:id>')
def sortir_du_stock(id):
    produit = ProduitFini.query.get_or_404(id)
    produit.statut = 'SORTI'
    produit.date_statut = datetime.now()
    db.session.commit()
    return redirect(url_for('stock'))

@app.route('/historique', methods=['GET'])
def historique():
    # 1. Récupération des filtres depuis l'URL
    type_id = request.args.get('type_id')
    calibre_id = request.args.get('calibre_id')
    cond_id = request.args.get('cond_id')
    parcelle_id = request.args.get('parcelle_id')
    client_id = request.args.get('client_id')
    bl_numero = request.args.get('bl_numero')  # Nouveau : Filtrage par numéro de BL
    statut = request.args.get('statut')
    date_debut = request.args.get('date_debut')
    date_fin = request.args.get('date_fin')

    # 2. Requête de base
    query = ProduitFini.query

    # Jointures nécessaires si on filtre par Client ou par numéro de BL
    if client_id or bl_numero:
        query = query.join(DetailLivraison).join(Livraison)

    if client_id:
        query = query.filter(Livraison.client_id == client_id)
    
    if bl_numero:
        query = query.filter(Livraison.numero_bl == bl_numero)

    # 3. Application des filtres techniques
    if type_id:
        query = query.filter(ProduitFini.type_id == type_id)
    if calibre_id:
        query = query.filter(ProduitFini.calibre_id == calibre_id)
    if cond_id:
        query = query.filter(ProduitFini.cond_id == cond_id)
    if parcelle_id:
        query = query.filter(ProduitFini.parcelle_id == parcelle_id)
    if statut:
        query = query.filter(ProduitFini.statut == statut)
    
    # Filtre par date
    if date_debut:
        d_debut = datetime.strptime(date_debut, '%Y-%m-%d')
        query = query.filter(ProduitFini.date_creation >= d_debut)
    if date_fin:
        d_fin = datetime.strptime(date_fin, '%Y-%m-%d')
        # On inclut toute la journée de fin
        d_fin = d_fin.replace(hour=23, minute=59, second=59)
        query = query.filter(ProduitFini.date_creation <= d_fin)

    produits = query.order_by(ProduitFini.date_creation.desc()).all()

    # 4. Retour des données au template
    return render_template('historique.html', 
                           produits=produits,
                           types=TypeProduit.query.all(),
                           calibres=Calibre.query.all(),
                           conds=TypeConditionnement.query.all(),
                           parcelles=Parcelle.query.all(),
                           clients=Client.query.all(),
                           # On envoie la liste des BL pour le datalist (triés par les plus récents)
                           livraisons=Livraison.query.order_by(Livraison.date_livraison.desc()).all())




@app.route('/tarifs', methods=['GET', 'POST'])
def gestion_tarifs():
    if request.method == 'POST':
        client_id = request.form.get('client_id')
        type_id = request.form.get('type_id')
        variete_id = request.form.get('variete_id') or None
        calibre_id = request.form.get('calibre_id') or None
        cond_id = request.form.get('cond_id') or None
        prix_ht = request.form.get('prix_ht')

        # Recherche d'un tarif existant
        tarif = TarifClient.query.filter_by(
            client_id=client_id, type_id=type_id, variete_id=variete_id, 
            calibre_id=calibre_id, cond_id=cond_id
        ).first()

        if tarif:
            tarif.prix_ht = float(prix_ht)
        else:
            nouveau_tarif = TarifClient(
                client_id=client_id, type_id=type_id, variete_id=variete_id,
                calibre_id=calibre_id, cond_id=cond_id, prix_ht=float(prix_ht)
            )
            db.session.add(nouveau_tarif)
        
        db.session.commit()
        return redirect(url_for('gestion_tarifs', client_id=client_id)) # On reste sur le client filtré

    # --- PARTIE AFFICHAGE (GET) ---
    f_client = request.args.get('client_id') # Récupère le filtre depuis l'URL
    
    query = TarifClient.query
    if f_client:
        query = query.filter_by(client_id=f_client)
    
    tarifs = query.all()
    
    return render_template('tarifs.html', 
                           clients=Client.query.all(), 
                           types=TypeProduit.query.all(), 
                           varietes=Variete.query.all(), 
                           calibres=Calibre.query.all(), 
                           conditionnements=TypeConditionnement.query.all(), 
                           tarifs=tarifs,
                           f_client=f_client)

# Route pour supprimer un tarif (si tu ne l'avais pas déjà)



@app.route('/supprimer_tarif/<int:id>')
def supprimer_tarif(id):
    tarif = TarifClient.query.get_or_404(id)
    db.session.delete(tarif)
    db.session.commit()
    return redirect(url_for('gestion_tarifs'))





@app.route('/referentiel')
def referentiel():
    return render_template('referentiel.html', 
        societe=Societe.query.first(), producteurs=Producteur.query.all(),
        parcelles=Parcelle.query.all(), types_prod=TypeProduit.query.all(),
        varietes=Variete.query.all(), conds=TypeConditionnement.query.all(),
        calibres=Calibre.query.all())


@app.route('/ajouter_produit', methods=['GET', 'POST'])
def ajouter_produit():
    if request.method == 'POST':
        poids_u = float(request.form['poids_unite_reel'])
        nb = int(request.form['nb_unites'])
        
        # 1. Enregistrement du lot global en base
        nouveau = ProduitFini(
            type_id=int(request.form['type_id']),
            variete_id=int(request.form['variete_id']),
            calibre_id=int(request.form['calibre_id']),
            parcelle_id=int(request.form['parcelle_id']),
            cond_id=int(request.form['cond_id']),
            nb_unites=nb,
            poids_unite_reel=poids_u,
            poids_total=nb * poids_u,
            statut='EN_STOCK'
        )
        db.session.add(nouveau)
        db.session.commit()
        
        # 2. Génération du PDF avec UN PAGE PAR UNITÉ
        generer_etiquettes_multiples(nouveau)
        
        return redirect(url_for('stock'))
    return render_template('ajouter_produit.html', 
        types_prod=TypeProduit.query.all(), parcelles=Parcelle.query.all(), 
        conds=TypeConditionnement.query.all(), calibres=Calibre.query.all())

@app.route('/parametres', methods=['GET', 'POST'])
def parametres():
    societe = Societe.query.first()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_societe':
            if not societe:
                societe = Societe()
                db.session.add(societe)
            
            # Récupération et mise à jour de TOUS les champs
            societe.nom = request.form.get('nom')
            societe.adresse = request.form.get('adresse')
            societe.code_postal = request.form.get('code_postal') # On ajoute cette ligne
            societe.ville = request.form.get('ville')             # Et celle-ci
            societe.coc_number = request.form.get('coc_number')
            
            db.session.commit()
            return redirect(url_for('parametres'))
        elif action == 'add_producteur':
            db.session.add(Producteur(nom=request.form['nom'], ggn=request.form['ggn']))
        elif action == 'add_parcelle':
            db.session.add(Parcelle(nom=request.form['nom'], producteur_id=request.form['prod_id']))
        elif action == 'add_type_produit':
            db.session.add(TypeProduit(nom=request.form['nom']))
        elif action == 'add_variete':
            db.session.add(Variete(nom=request.form['nom'], type_produit_id=request.form['type_id']))
        elif action == 'add_calibre':
            db.session.add(Calibre(nom=request.form['nom']))
        elif action == 'add_cond':
            db.session.add(TypeConditionnement(nom=request.form['nom'], poids_unite=float(request.form['poids'])))
        db.session.commit()
        return redirect(url_for('parametres'))
    return render_template('parametres.html', 
        societe=Societe.query.first(), producteurs=Producteur.query.all(),
        parcelles=Parcelle.query.all(), types_prod=TypeProduit.query.all(),
        varietes=Variete.query.all(), conds=TypeConditionnement.query.all(),
        calibres=Calibre.query.all())


#@app.route('/ajouter_client', methods=['POST'])
#def ajouter_client():
    if request.method == 'POST':
        nom = request.form.get('nom')
        email_principal = request.form.get('email')
        email2 = request.form.get('email2') # On récupère le 2ème
        email3 = request.form.get('email3') # On récupère le 3ème
        

        # On crée le nouvel objet Client avec les 3 emails
        nouveau_client = Client(
            nom=nom,
            email=email_principal,
            email2=email2,
            email3=email3,
            adresse=request.form.get('adresse'),
            ville=request.form.get('ville'),
            code_postal=request.form.get('code_postal'),
            telephone=request.form.get('telephone')
        )
        
        db.session.add(nouveau_client)
        db.session.commit()
        return redirect(url_for('referentiel'))


    
    clients = Client.query.order_by(Client.nom).all()
    return render_template('clients.html', clients=clients)

@app.route('/clients', methods=['GET', 'POST']) # Remplacez par le nom réel de votre route
def gestion_clients():
    if request.method == 'POST':
        # Récupération de TOUS les champs du formulaire
        nouveau_client = Client(
            nom=request.form.get('nom'),
            adresse=request.form.get('adresse'),
            ville=request.form.get('ville'),
            code_postal=request.form.get('code_postal'),
            telephone=request.form.get('telephone'),
            email=request.form.get('email'),    # Email 1
            email2=request.form.get('email2'),  # Email 2
            email3=request.form.get('email3')   # Email 3
        )
        db.session.add(nouveau_client)
        db.session.commit()
        return redirect(url_for('gestion_clients')) # Recharge la page pour voir le nouveau client
    
    clients = Client.query.all()
    return render_template('clients.html', clients=clients)

@app.route('/supprimer_client/<int:id>')
def supprimer_client(id):
    client = Client.query.get_or_404(id)
    db.session.delete(client)
    db.session.commit()
    return redirect(url_for('gestion_clients'))


@app.route('/nouvelle_livraison', methods=['GET', 'POST'])
def nouvelle_livraison():
    if request.method == 'POST':
        try:
            client_id = request.form.get('client_id')
            transporteur_id = request.form.get('transporteur_id')
            date_livraison_str = request.form.get('date_livraison')
            date_livraison = datetime.strptime(date_livraison_str, '%Y-%m-%d')
            obs = request.form.get('observations')

            # 1. Génération robuste du numéro de BL
            annee = datetime.now().year
            prefixe = f"BL-{annee}-"
            derniere = Livraison.query.filter(Livraison.numero_bl.like(f"{prefixe}%"))\
                                      .order_by(Livraison.id.desc()).first()
            
            nouveau_index = 1
            if derniere and derniere.numero_bl:
                try:
                    nouveau_index = int(derniere.numero_bl.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    nouveau_index = 1
            
            num_bl = f"{prefixe}{nouveau_index:03d}"

            # Création de l'entête
            nouvelle_bl = Livraison(
                client_id=client_id,
                transporteur_id=transporteur_id,
                date_livraison=date_livraison,
                numero_bl=num_bl,
                observations=obs
            )

            db.session.add(nouvelle_bl)
            db.session.flush()

            # 2. Gestion Stock (Lots existants) - MODIFIÉ POUR LE POIDS
            lots_selectionnes = request.form.getlist('lots')
            for lot_id in lots_selectionnes:
                prix_ht = request.form.get(f'prix_{lot_id}', type=float)
                # RECUPERATION DU POIDS MODIFIÉ DANS LE FORMULAIRE
                poids_saisi = request.form.get(f'poids_lot_{lot_id}', type=float)
                
                produit = db.session.get(ProduitFini, int(lot_id))
                if produit:
                    # Mise à jour du poids si une valeur a été saisie
                    if poids_saisi is not None:
                        produit.poids_total = poids_saisi
                    
                    produit.statut = 'EXPEDIE'
                    
                    db.session.add(DetailLivraison(
                        livraison_id=nouvelle_bl.id,
                        produit_id=produit.id,
                        prix_unitaire_ht=prix_ht or 0.0
                    ))

            # 3. Gestion Hors-Stock (Saisie express) - Inchangé
            hs_types = request.form.getlist('hs_type[]')
            hs_varietes = request.form.getlist('hs_variete[]')
            hs_calibres = request.form.getlist('hs_calibre[]')
            hs_conds = request.form.getlist('hs_cond[]')
            hs_poids = request.form.getlist('hs_poids[]')
            hs_prix = request.form.getlist('hs_prix[]')
            hs_parcelles = request.form.getlist('hs_parcelle[]')
            hs_nb = request.form.getlist('hs_nb[]')

            for i in range(len(hs_types)):
                if hs_types[i]:
                    nouveau_p = ProduitFini(
                        type_id=hs_types[i],
                        variete_id=hs_varietes[i] if hs_varietes[i] else None,
                        calibre_id=hs_calibres[i] if hs_calibres[i] else None,
                        cond_id=hs_conds[i] if hs_conds[i] else None,
                        parcelle_id=hs_parcelles[i] if hs_parcelles[i] else None,
                        nb_unites=int(hs_nb[i]) if hs_nb[i] else 0,
                        poids_total=float(hs_poids[i]) if hs_poids[i] else 0.0,
                        statut='EXPEDIE'
                    )
                    db.session.add(nouveau_p)
                    db.session.flush()
                    
                    db.session.add(DetailLivraison(
                        livraison_id=nouvelle_bl.id,
                        produit_id=nouveau_p.id,
                        prix_unitaire_ht=float(hs_prix[i]) if hs_prix[i] else 0.0
                    ))

            db.session.commit()
            generer_pdf_bl(nouvelle_bl)
            
            flash(f"BL {nouvelle_bl.numero_bl} créé avec succès !", "success")
            return redirect(url_for('historique_livraisons'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création du BL : {str(e)}', 'danger')

    # --- PARTIE GET ---
    clients = Client.query.all()
    transporteurs = Transporteur.query.all()
    stock = ProduitFini.query.filter_by(statut='EN_STOCK').all()
    types = TypeProduit.query.all()
    varietes = Variete.query.all()
    calibres = Calibre.query.all()
    conditionnements = TypeConditionnement.query.all()
    parcelles = Parcelle.query.all()
    date_defaut = datetime.now().strftime('%Y-%m-%d')

    return render_template('nouvelle_livraison.html', 
                            clients=clients, transporteurs=transporteurs,
                            stock=stock, types=types, varietes=varietes,
                            calibres=calibres, conditionnements=conditionnements,
                            parcelles=parcelles, date_defaut=date_defaut)

@app.route('/expedition_terminee/<int:id>')
def expedition_terminee(id):
    livraison = Livraison.query.get_or_404(id)
    # On génère le PDF
    pdf_path = generer_pdf_bl(livraison)
    
    # On prépare le mail
    try:
        msg = Message(f"Bon de Livraison {livraison.numero_bl}",
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[livraison.client_rel.email])
        
        msg.body = f"Bonjour {livraison.client_rel.nom},\n\nVeuillez trouver ci-joint le bon de livraison pour l'expédition du {livraison.date_livraison.strftime('%d/%m/%Y')}.\n\nTransporteur : {livraison.transporteur_rel.nom}\n\nCordialement."
        
        with app.open_resource(pdf_path) as fp:
            msg.attach(f"{livraison.numero_bl}.pdf", "application/pdf", fp.read())
        
        mail.send(msg)
        flash("Livraison enregistrée et email envoyé !", "success")
    except Exception as e:
        flash(f"Livraison enregistrée mais erreur d'envoi mail : {e}", "warning")
        
    return redirect(url_for('stock'))

@app.route('/transporteurs', methods=['GET', 'POST'])
def gestion_transporteurs():
    if request.method == 'POST':
        nouveau = Transporteur(
            nom=request.form.get('nom'),
            telephone=request.form.get('telephone'),
            email=request.form.get('email')
        )
        db.session.add(nouveau)
        db.session.commit()
        return redirect(url_for('gestion_transporteurs'))
    
    transporteurs = Transporteur.query.order_by(Transporteur.nom).all()
    return render_template('transporteurs.html', transporteurs=transporteurs)





@app.route('/modifier_transporteur/<int:id>', methods=['GET', 'POST'])
def modifier_transporteur(id):
    t = Transporteur.query.get_or_404(id)
    if request.method == 'POST':
        t.nom = request.form.get('nom')
        t.telephone = request.form.get('telephone')
        t.email = request.form.get('email')
        db.session.commit()
        return redirect(url_for('gestion_transporteurs'))
    return render_template('modifier_transporteur.html', t=t)

@app.route('/supprimer_transporteur/<int:id>')
def supprimer_transporteur(id):
    t = Transporteur.query.get_or_404(id)
    db.session.delete(t)
    db.session.commit()
    return redirect(url_for('gestion_transporteurs'))

@app.route('/nouvelle_parcelle', methods=['GET', 'POST'])
def nouvelle_parcelle():
    if request.method == 'POST':
        nom = request.form.get('nom')
        producteur_id = request.form.get('producteur_id')
        ggn = request.form.get('ggn') # On récupère le GGN saisi ou auto-rempli
        
        n_parcelle = Parcelle(nom=nom, producteur_id=producteur_id, ggn=ggn)
        db.session.add(n_parcelle)
        db.session.commit()
        return redirect(url_for('configuration')) # Ou votre page de gestion

    producteurs = Producteur.query.all()
    return render_template('nouvelle_parcelle.html', producteurs=producteurs)

@app.route('/config_societe', methods=['GET', 'POST'])
def config_societe():
    soc = Societe.query.first()
    if request.method == 'POST':
        if not soc:
            soc = Societe()
        soc.nom = request.form.get('nom')
        soc.adresse = request.form.get('adresse')
        soc.code_postal = request.form.get('code_postal')
        soc.ville = request.form.get('ville')
        soc.coc_number = request.form.get('coc_number')
        
        db.session.add(soc)
        db.session.commit()
        return redirect(url_for('stock'))
        
    return render_template('config_societe.html', soc=soc)



from datetime import datetime, timedelta

@app.route('/historique_livraisons')
def historique_livraisons():
    # 1. Calcul des dates par défaut (si non présentes dans l'URL)
    aujourdhui = datetime.now().date()
    # On garde votre logique : 1 mois avant jusqu'à aujourd'hui
    un_mois_avant = (aujourdhui - timedelta(days=30)).strftime('%Y-%m-%d')
    date_jour_str = aujourdhui.strftime('%Y-%m-%d')

    # 2. Récupération des filtres depuis l'URL
    f_client = request.args.get('client_id')
    f_numero_bl = request.args.get('numero_bl')  # <-- Nouveau filtre
    f_debut = request.args.get('date_debut', un_mois_avant)
    f_fin = request.args.get('date_fin', date_jour_str)
    f_statut_facture = request.args.get('statut_facture')

    query = Livraison.query

    # 3. Application des filtres
    if f_client and f_client != "":
        query = query.filter(Livraison.client_id == int(f_client))
    
    # Filtre par numéro de BL (recherche partielle insensible à la casse)
    if f_numero_bl:
        query = query.filter(Livraison.numero_bl.ilike(f'%{f_numero_bl}%'))
    
    if f_debut:
        query = query.filter(Livraison.date_livraison >= f_debut)
    if f_fin:
        # Note : on ajoute l'heure de fin pour couvrir toute la journée si c'est un DateTime
        query = query.filter(Livraison.date_livraison <= f_fin + " 23:59:59")
    
    if f_statut_facture == 'non_facture':
        query = query.filter((Livraison.numero_facture == None) | (Livraison.numero_facture == ''))
    elif f_statut_facture == 'facture':
        query = query.filter(Livraison.numero_facture != None, Livraison.numero_facture != '')

    # 4. Exécution et tri
    livraisons = query.order_by(Livraison.date_livraison.desc()).all()
    clients = Client.query.all()
    
    return render_template('historique_livraisons.html', 
                           livraisons=livraisons, 
                           clients=clients, 
                           f_client=f_client,
                           f_numero_bl=f_numero_bl,
                           f_debut=f_debut, 
                           f_fin=f_fin,
                           f_statut_facture=f_statut_facture)


@app.route('/update_facture/<int:livraison_id>', methods=['POST'])
def update_facture(livraison_id):
    livraison = Livraison.query.get_or_404(livraison_id)
    livraison.numero_facture = request.form.get('numero_facture')
    db.session.commit()
    return redirect(request.referrer or url_for('historique_livraisons'))



@app.route('/voir_pdf/<int:id>')
def voir_pdf(id):
    livraison = Livraison.query.get_or_404(id)
    # On génère le PDF au vol (ou on le récupère s'il existe déjà)
    pdf_path = generer_pdf_bl(livraison)
    return send_file(pdf_path)





# --- ROUTES MODIFICATION ---

@app.route('/modifier_tarif/<int:id>', methods=['POST'])
def modifier_tarif(id):
    tarif = TarifClient.query.get_or_404(id)
    nouveau_prix = request.form.get('prix')
    
    if nouveau_prix:
        try:
            tarif.prix_unitaire = float(nouveau_prix)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Erreur : {e}")
            
    # On redirige vers la page des tarifs en gardant le filtre client si possible
    return redirect(url_for('gestion_tarifs', client_id=tarif.client_id))


@app.route('/modifier_producteur/<int:id>', methods=['GET', 'POST'])
def modifier_producteur(id):
    item = Producteur.query.get_or_404(id)
    if request.method == 'POST':
        item.nom, item.ggn = request.form['nom'], request.form['ggn']
        db.session.commit()
        return redirect(url_for('referentiel'))
    return render_template('modifier_producteur.html', prod=item)

@app.route('/modifier_calibre/<int:id>', methods=['GET', 'POST'])
def modifier_calibre(id):
    item = Calibre.query.get_or_404(id)
    if request.method == 'POST':
        item.nom = request.form['nom']
        db.session.commit()
        return redirect(url_for('referentiel'))
    return render_template('modifier_type.html', type_prod=item) # Réutilise le template simple
# --- AJOUT DES ROUTES DE MODIFICATION MANQUANTES ---

@app.route('/modifier_parcelle/<int:id>', methods=['GET', 'POST'])
def modifier_parcelle(id):
    item = Parcelle.query.get_or_404(id)
    
    if request.method == 'POST':
        # Mise à jour des champs existants
        item.nom = request.form['nom']
        item.producteur_id = request.form['prod_id']
        
        # AJOUT : Récupération et sauvegarde du GGN spécifique à la parcelle
        # On utilise .get() pour plus de sécurité
        item.ggn = request.form.get('ggn')
        
        db.session.commit()
        return redirect(url_for('referentiel'))
    
    producteurs = Producteur.query.all()
    return render_template('modifier_parcelle.html', parcelle=item, producteurs=producteurs)

@app.route('/modifier_conditionnement/<int:id>', methods=['GET', 'POST'])
def modifier_conditionnement(id):
    item = TypeConditionnement.query.get_or_404(id)
    if request.method == 'POST':
        item.nom = request.form['nom']
        item.poids_unite = float(request.form['poids'])
        db.session.commit()
        return redirect(url_for('referentiel'))
    return render_template('modifier_cond.html', cond=item)

@app.route('/modifier_type/<int:id>', methods=['GET', 'POST'])
def modifier_type(id):
    item = TypeProduit.query.get_or_404(id)
    if request.method == 'POST':
        item.nom = request.form['nom']
        db.session.commit()
        return redirect(url_for('referentiel'))
    return render_template('modifier_type.html', type_prod=item)

@app.route('/modifier_variete/<int:id>', methods=['GET', 'POST'])
def modifier_variete(id):
    item = Variete.query.get_or_404(id)
    if request.method == 'POST':
        item.nom = request.form['nom']
        item.type_produit_id = request.form['type_id']
        db.session.commit()
        return redirect(url_for('referentiel'))
    types = TypeProduit.query.all()
    return render_template('modifier_variete.html', variete=item, types_prod=types)

@app.route('/modifier_client/<int:id>', methods=['GET', 'POST'])
def modifier_client(id):
    client = Client.query.get_or_404(id)
    if request.method == 'POST':
        client.nom = request.form.get('nom')
        client.adresse = request.form.get('adresse')
        client.ville = request.form.get('ville')
        client.code_postal = request.form.get('code_postal')
        client.telephone = request.form.get('telephone')
        client.ggn_client = request.form.get('ggn_client')
        # On met à jour les 3 adresses mail
        client.email = request.form.get('email')
        client.email2 = request.form.get('email2')
        client.email3 = request.form.get('email3')

        db.session.commit()
        return redirect(url_for('gestion_clients'))
    
    return render_template('modifier_client.html', client=client)


@app.route('/modifier_produit/<int:id>', methods=['GET', 'POST'])
def modifier_produit(id):
    produit = ProduitFini.query.get_or_404(id)
    
    if request.method == 'POST':
        # Récupération des données du formulaire
        produit.type_id = request.form.get('type_id')
        produit.variete_id = request.form.get('variete_id')
        produit.calibre_id = request.form.get('calibre_id')
        produit.cond_id = request.form.get('cond_id')
        produit.parcelle_id = request.form.get('parcelle_id')
        produit.nb_unites = int(request.form.get('nb_unites'))
        produit.poids_total = float(request.form.get('poids_total'))
        
        db.session.commit()
        return redirect(url_for('stock'))

    # Pour le formulaire (GET)
    types = TypeProduit.query.all()
    varietes = Variete.query.all()
    calibres = Calibre.query.all()
    conditionnements = TypeConditionnement.query.all()
    parcelles = Parcelle.query.all()
    
    return render_template('modifier_produit.html', 
                           produit=produit,
                           types=types,
                           varietes=varietes,
                           calibres=calibres,
                           conditionnements=conditionnements,
                           parcelles=parcelles)


@app.route('/modifier_livraison/<int:id>', methods=['GET', 'POST'])
def modifier_livraison(id):
    livraison = db.session.get(Livraison, id)
    if not livraison:
        abort(404)
    
    if request.method == 'POST':
        try:
            action = request.form.get('action')

            # 1. Infos générales
            t_id = request.form.get('transporteur_id')
            if t_id:
                livraison.transporteur_id = int(t_id)
            
            livraison.client_id = request.form.get('client_id')
            
            date_saisie = request.form.get('date_livraison')
            if date_saisie:
                livraison.date_livraison = datetime.strptime(date_saisie, '%Y-%m-%d')

            # 2. Mise à jour des lignes existantes
            for d in livraison.details:
                # MISE À JOUR DU PRIX (Utilise prix_{{d.id}})
                nouveau_prix = request.form.get(f'prix_{d.id}')
                if nouveau_prix is not None:
                    d.prix_unitaire_ht = float(nouveau_prix)
                
                # MISE À JOUR DU POIDS (Utilise le name EXACT de votre template : poids_lot_{{d.produit_id}})
                # C'est ici que se faisait la liaison avec la base de données
                poids_saisi = request.form.get(f'poids_lot_{d.produit_id}')
                if poids_saisi is not None:
                    # On met à jour le poids sur le produit lié à cette ligne de BL
                    d.produit_rel.poids_total = float(poids_saisi)

                # 3. AJOUT : Mise à jour du NOMBRE DE COLIS
                colis_saisi = request.form.get(f'colis_{d.id}')
                if colis_saisi is not None:
                    d.produit_rel.nb_unites = int(colis_saisi)
            
            # 3. Ajout d'un lot "Hors Stock"
            nouveau_type = request.form.get('nouveau_type_id')
            if nouveau_type:
                nouveau_p = ProduitFini(
                    type_id=nouveau_type,
                    variete_id=request.form.get('nouveau_variete_id') or None,
                    calibre_id=request.form.get('nouveau_calibre_id') or None,
                    cond_id=request.form.get('nouveau_cond_id') or None,
                    parcelle_id=request.form.get('nouveau_parcelle_id') or None,
                    nb_unites=int(request.form.get('nouveau_nb') or 0),
                    poids_total=float(request.form.get('nouveau_poids') or 0),
                    statut='EXPEDIE'
                )
                db.session.add(nouveau_p)
                db.session.flush()

                nouveau_detail = DetailLivraison(
                    livraison_id=livraison.id,
                    produit_id=nouveau_p.id,
                    prix_unitaire_ht=float(request.form.get('nouveau_prix') or 0)
                )
                db.session.add(nouveau_detail)

            db.session.commit()
            db.session.refresh(livraison)
            
            # Régénérer le PDF avec les poids et prix modifiés
            generer_pdf_bl(livraison)

            if action == 'ajouter_hors_stock':
                flash("Lot ajouté au BL", "success")
                return redirect(url_for('modifier_livraison', id=id) + '#nouveau_lot_form')
            else:
                flash("Livraison mise à jour et PDF actualisé", "primary")
                return redirect(url_for('historique_livraisons'))

        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la modification : {str(e)}", "danger")
            print(f"ERREUR MODIF : {str(e)}")

    return render_template('modifier_livraison.html', 
                           livraison=livraison, 
                           clients=Client.query.all(), 
                           transporteurs=Transporteur.query.all(),
                           types=TypeProduit.query.all(),
                           varietes=Variete.query.all(),
                           calibres=Calibre.query.all(),
                           conditionnements=TypeConditionnement.query.all(),
                           parcelles=Parcelle.query.all())



@app.route('/get_tarif_prix')
def get_tarif_prix():
    try:
        # 1. Récupération des IDs et conversion en Entiers (indispensable pour SQLAlchemy)
        # On traite les chaînes vides comme None pour la base de données
        def to_int(val):
            if val and str(val).strip() and str(val) != 'None':
                return int(val)
            return None

        c_id = to_int(request.args.get('client_id'))
        t_id = to_int(request.args.get('type_id'))
        v_id = to_int(request.args.get('variete_id'))
        cal_id = to_int(request.args.get('calibre_id'))
        cond_id = to_int(request.args.get('cond_id'))

        # 2. Requête avec filtre STRICT sur toutes les colonnes
        # On utilise filter_by pour les colonnes classiques
        tarif = TarifClient.query.filter_by(
            client_id=c_id,
            type_id=t_id,
            variete_id=v_id,
            calibre_id=cal_id,
            cond_id=cond_id
        ).first()

        # 3. Réponse : On renvoie le prix si trouvé, sinon 0.000
        if tarif:
            # On s'assure que le retour est bien un float pour le JavaScript
            return jsonify({'prix': float(tarif.prix_ht)})
        
        # Si rien n'est trouvé : Retour strict 0
        return jsonify({'prix': 0.000})

    except Exception as e:
        print(f"Erreur get_tarif_prix : {e}")
        # En cas d'erreur technique, on renvoie aussi 0 pour ne pas bloquer le JS
        return jsonify({'prix': 0.000, 'error': str(e)})


@app.route('/supprimer_ligne_bl/<int:detail_id>')
def supprimer_ligne_bl(detail_id):
    detail = DetailLivraison.query.get_or_404(detail_id)
    livraison_id = detail.livraison_id
    
    # On récupère le produit lié pour le remettre en stock
    produit = ProduitFini.query.get(detail.produit_id)
    if produit:
        produit.statut = 'EN_STOCK'
    
    # On supprime la ligne de détail
    db.session.delete(detail)
    db.session.commit()
    
    # On régénère le PDF sans cette ligne
    livraison = Livraison.query.get(livraison_id)
    generer_pdf_bl(livraison)
    
    return redirect(url_for('modifier_livraison', id=livraison_id))



@app.route('/supprimer_livraison/<int:id>')
def supprimer_livraison(id):
    # Utilisation de db.session.get pour être plus moderne et stable
    livraison = db.session.get(Livraison, id)
    if not livraison:
        flash("Livraison introuvable.", "danger")
        return redirect(url_for('historique_livraisons'))
    
    try:
        # On récupère le numéro de BL avant suppression pour le message flash
        num_bl = livraison.numero_bl
        
        # 1. On boucle sur les détails
        for d in livraison.details_items: # Utilisation du backref 'details_items' défini dans votre classe
            p = d.produit_rel 
            if p:
                # C'est ICI que tout se joue :
                # On remet EXACTEMENT le même mot que celui filtré dans la page Stock
                p.statut = 'EN_STOCK'
        
        # 2. Suppression de la livraison
        db.session.delete(livraison)
        db.session.commit()
        
        flash(f"Livraison {num_bl} supprimée. Les lots sont de nouveau disponibles en stock.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la suppression : {str(e)}", "danger")
        
    return redirect(url_for('historique_livraisons'))


@app.route('/get_poids_conditionnement')
def get_poids_conditionnement():
    cond_id = request.args.get('cond_id')
    # Remplacez TypeConditionnement par le nom exact de votre classe si différent
    cond = TypeConditionnement.query.get(cond_id)
    
    if cond:
        # Remplacez 'poids_unitaire' par le nom de votre colonne dans la table conditionnement
        return jsonify({'poids': getattr(cond, 'poids_unite', 0)})
    return jsonify({'poids': 0})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)