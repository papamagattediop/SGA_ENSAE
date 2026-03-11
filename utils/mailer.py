# ============================================================
#  SGA ENSAE — utils/mailer.py
#  Notifications email via Gmail SMTP
#  Python 3.11
# ============================================================

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

MAIL_ADDRESS  = os.getenv("MAIL_ADDRESS", "")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
SMTP_HOST     = "smtp.gmail.com"
SMTP_PORT     = 587
APP_NAME      = "SGA ENSAE"

BLEU = "#003580"
VERT = "#006B3F"
OR   = "#F5A623"


# ============================================================
#  UTILITAIRE ENVOI
# ============================================================

def send_email(to: str, subject: str, html_body: str) -> tuple[bool, str]:
    """
    Envoie un email HTML via Gmail SMTP.
    Retourne (succes, message_erreur).
    """
    if not MAIL_ADDRESS or not MAIL_PASSWORD:
        return False, "Variables MAIL_ADDRESS ou MAIL_PASSWORD non configurees dans .env"

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[{APP_NAME}] {subject}"
        msg["From"]    = f"{APP_NAME} <{MAIL_ADDRESS}>"
        msg["To"]      = to

        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(MAIL_ADDRESS, MAIL_PASSWORD.replace(" ", ""))
            server.sendmail(MAIL_ADDRESS, to, msg.as_string())

        return True, ""

    except smtplib.SMTPAuthenticationError:
        return False, "Erreur authentification Gmail — verifiez MAIL_ADDRESS et MAIL_PASSWORD dans .env"
    except smtplib.SMTPException as e:
        return False, f"Erreur SMTP : {str(e)}"
    except Exception as e:
        return False, f"Erreur inattendue : {str(e)}"


# ============================================================
#  TEMPLATE HTML BASE
# ============================================================

def base_template(titre: str, contenu: str, couleur_header: str = BLEU) -> str:
    return f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{titre}</title>
    </head>
    <body style="margin:0;padding:0;background:#F4F6F9;font-family:'Helvetica Neue',Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0"
               style="background:#F4F6F9;padding:32px 0;">
            <tr>
                <td align="center">
                    <table width="580" cellpadding="0" cellspacing="0"
                           style="background:#ffffff;border-radius:12px;
                                  box-shadow:0 2px 12px rgba(0,0,0,0.08);
                                  overflow:hidden;">

                        <!-- Header -->
                        <tr>
                            <td style="background:{couleur_header};padding:24px 32px;">
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td>
                                            <span style="color:#ffffff;font-size:1.2rem;
                                                         font-weight:800;letter-spacing:0.5px;">
                                                {APP_NAME}
                                            </span><br>
                                            <span style="color:rgba(255,255,255,0.65);
                                                         font-size:0.75rem;">
                                                Systeme de Gestion Academique — ENSAE Dakar
                                            </span>
                                        </td>
                                        <td align="right">
                                            <span style="background:{OR};color:{BLEU};
                                                         padding:4px 12px;border-radius:999px;
                                                         font-size:0.72rem;font-weight:700;">
                                                Notification
                                            </span>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <!-- Barre doree -->
                        <tr>
                            <td style="background:{OR};height:3px;"></td>
                        </tr>

                        <!-- Corps -->
                        <tr>
                            <td style="padding:32px;">
                                <h2 style="color:{BLEU};font-size:1.1rem;font-weight:700;
                                           margin:0 0 16px;">{titre}</h2>
                                {contenu}
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="background:#f9fafb;padding:16px 32px;
                                       border-top:1px solid #e5e7eb;">
                                <p style="color:#9ca3af;font-size:0.72rem;margin:0;
                                          text-align:center;">
                                    Cet email a ete envoye automatiquement par {APP_NAME}.<br>
                                    Ne pas repondre directement a cet email.
                                </p>
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


# ============================================================
#  EMAILS PLANNING
# ============================================================

def _tableau_seances_html(seances: list, couleur: str, colonnes: list) -> str:
    """
    Helper interne : génère le HTML d'un tableau de séances.
    colonnes : liste de clés parmi ['jour', 'date', 'module', 'enseignant', 'heure_debut', 'heure_fin']
    Les colonnes 'heure_debut' et 'heure_fin' sont fusionnées en 'Horaire'.
    """
    entetes = {
        "jour"      : "Jour",
        "date"      : "Date",
        "module"    : "Module",
        "enseignant": "Enseignant",
        "horaire"   : "Horaire",
    }

    # Construire les en-têtes (remplacer heure_debut+heure_fin par horaire)
    cols_affichees = []
    for c in colonnes:
        if c == "heure_debut":
            cols_affichees.append("horaire")
        elif c == "heure_fin":
            continue
        else:
            cols_affichees.append(c)

    ths = "".join([
        f"""<th style="padding:10px 10px;font-size:0.72rem;color:{couleur};
                       text-align:left;font-weight:700;text-transform:uppercase;
                       border-bottom:1px solid #e5e7eb;">
                {entetes.get(c, c)}
            </th>"""
        for c in cols_affichees
    ])

    if not seances:
        nb_cols = len(cols_affichees)
        rows_html = f"""
        <tr>
            <td colspan="{nb_cols}" style="padding:16px;text-align:center;
                                           font-size:0.82rem;color:#9ca3af;font-style:italic;">
                Aucune séance enregistrée.
            </td>
        </tr>"""
    else:
        rows_html = ""
        for s in seances:
            tds = ""
            for c in cols_affichees:
                if c == "horaire":
                    val   = f"{s.get('heure_debut', '-')} – {s.get('heure_fin', '-')}"
                    style = "color:#6b7280;white-space:nowrap;"
                elif c in ("jour", "date"):
                    val   = s.get(c, '-')
                    style = "color:#6b7280;white-space:nowrap;"
                elif c == "enseignant":
                    val   = s.get(c) or "—"
                    style = "color:#6b7280;"
                else:
                    val   = s.get(c, '-')
                    style = "color:#374151;"
                tds += f'<td style="padding:8px 10px;font-size:0.80rem;{style}">{val}</td>'
            rows_html += f'<tr style="border-bottom:1px solid #f3f4f6;">{tds}</tr>'

    return f"""
        <table width="100%" cellpadding="0" cellspacing="0"
               style="border:1px solid #e5e7eb;border-radius:8px;
                      overflow:hidden;margin-bottom:24px;border-collapse:collapse;">
            <tr style="background:{couleur}12;">{ths}</tr>
            {rows_html}
        </table>
    """


def email_planning_soumis(
    to: str,
    nom_resp_filiere: str,
    nom_resp_classe: str,
    classe: str,
    semaine: str,
    seances: list,
    planning_id: int
) -> tuple[bool, str]:
    """
    Email envoyé au responsable de filière quand un planning est soumis.
    seances : liste de dicts {module, enseignant, date, jour, heure_debut, heure_fin}
    """
    tableau = _tableau_seances_html(
        seances,
        couleur=BLEU,
        colonnes=["jour", "date", "module", "enseignant", "heure_debut", "heure_fin"]
    )

    contenu = f"""
        <p style="color:#374151;font-size:0.9rem;line-height:1.6;margin:0 0 16px;">
            Bonjour <strong>{nom_resp_filiere}</strong>,
        </p>
        <p style="color:#374151;font-size:0.9rem;line-height:1.6;margin:0 0 20px;">
            <strong>{nom_resp_classe}</strong> a soumis un planning pour la classe
            <strong>{classe}</strong> — semaine du <strong>{semaine}</strong>.
        </p>
        {tableau}
        <p style="color:#374151;font-size:0.875rem;margin:0 0 20px;">
            Connectez-vous sur <strong>{APP_NAME}</strong> pour valider,
            modifier ou rejeter ce planning.
        </p>
        <div style="text-align:center;margin-top:24px;">
            <a href="http://127.0.0.1:8050/planning"
               style="background:{BLEU};color:#ffffff;padding:12px 28px;
                      border-radius:8px;text-decoration:none;font-weight:700;
                      font-size:0.875rem;display:inline-block;">
                Voir le planning
            </a>
        </div>
    """
    html = base_template(f"Nouveau planning a valider — {classe}", contenu, BLEU)
    return send_email(to, f"Planning semaine {semaine} — {classe} en attente de validation", html)


def email_planning_valide(
    to: str,
    nom_resp_classe: str,
    classe: str,
    semaine: str,
    seances: list = None
) -> tuple[bool, str]:
    """
    Email envoyé au responsable de classe quand son planning est validé.
    Inclut le tableau récapitulatif des séances confirmées.
    """
    seances = seances or []

    tableau = _tableau_seances_html(
        seances,
        couleur=VERT,
        colonnes=["jour", "date", "module", "heure_debut", "heure_fin"]
    ) if seances else ""

    contenu = f"""
        <p style="color:#374151;font-size:0.9rem;line-height:1.6;margin:0 0 16px;">
            Bonjour <strong>{nom_resp_classe}</strong>,
        </p>
        <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;
                    padding:16px;margin-bottom:20px;">
            <p style="color:{VERT};font-weight:700;font-size:0.9rem;margin:0 0 6px;">
                ✅ Planning validé
            </p>
            <p style="color:#374151;font-size:0.875rem;margin:0;">
                Le planning de la classe <strong>{classe}</strong>
                pour la semaine du <strong>{semaine}</strong>
                a été <strong style="color:{VERT};">validé</strong>.
                Les enseignants ont été notifiés automatiquement.
            </p>
        </div>
        {f'<p style="color:#374151;font-size:0.85rem;font-weight:700;margin:0 0 8px;">Récapitulatif des séances confirmées :</p>' if seances else ""}
        {tableau}
        <div style="text-align:center;margin-top:24px;">
            <a href="http://127.0.0.1:8050/planning"
               style="background:{VERT};color:#ffffff;padding:12px 28px;
                      border-radius:8px;text-decoration:none;font-weight:700;
                      font-size:0.875rem;display:inline-block;">
                Voir mon planning
            </a>
        </div>
    """
    html = base_template(f"Planning valide — {classe}", contenu, VERT)
    return send_email(to, f"Planning semaine {semaine} — {classe} valide ✅", html)


def email_planning_rejete(
    to: str,
    nom_resp_classe: str,
    classe: str,
    semaine: str,
    commentaire: str
) -> tuple[bool, str]:
    """Email envoyé au responsable de classe quand son planning est rejeté."""
    contenu = f"""
        <p style="color:#374151;font-size:0.9rem;line-height:1.6;margin:0 0 16px;">
            Bonjour <strong>{nom_resp_classe}</strong>,
        </p>
        <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:8px;
                    padding:16px;margin-bottom:20px;">
            <p style="color:#ef4444;font-weight:700;font-size:0.9rem;margin:0 0 6px;">
                Planning rejeté
            </p>
            <p style="color:#374151;font-size:0.875rem;margin:0 0 10px;">
                Votre planning de la classe <strong>{classe}</strong>
                pour la semaine du <strong>{semaine}</strong>
                a été <strong style="color:#ef4444;">rejeté</strong>.
            </p>
            <p style="color:#374151;font-size:0.875rem;margin:0;">
                <strong>Commentaire :</strong> {commentaire or "Aucun commentaire."}
            </p>
        </div>
        <div style="text-align:center;margin-top:24px;">
            <a href="http://127.0.0.1:8050/planning"
               style="background:#ef4444;color:#ffffff;padding:12px 28px;
                      border-radius:8px;text-decoration:none;font-weight:700;
                      font-size:0.875rem;display:inline-block;">
                Corriger le planning
            </a>
        </div>
    """
    html = base_template(f"Planning rejeté — {classe}", contenu, "#ef4444")
    return send_email(to, f"Planning semaine {semaine} — {classe} rejeté", html)


def email_planning_modifie(
    to: str,
    nom_resp_classe: str,
    classe: str,
    semaine: str,
    commentaire: str
) -> tuple[bool, str]:
    """Email envoyé au responsable de classe quand son planning est modifié."""
    contenu = f"""
        <p style="color:#374151;font-size:0.9rem;line-height:1.6;margin:0 0 16px;">
            Bonjour <strong>{nom_resp_classe}</strong>,
        </p>
        <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:8px;
                    padding:16px;margin-bottom:20px;">
            <p style="color:#d97706;font-weight:700;font-size:0.9rem;margin:0 0 6px;">
                Planning à modifier
            </p>
            <p style="color:#374151;font-size:0.875rem;margin:0 0 10px;">
                Votre planning de la classe <strong>{classe}</strong>
                pour la semaine du <strong>{semaine}</strong>
                nécessite des <strong style="color:#d97706;">modifications</strong>.
            </p>
            <p style="color:#374151;font-size:0.875rem;margin:0;">
                <strong>Commentaire :</strong> {commentaire or "Aucun commentaire."}
            </p>
        </div>
        <div style="text-align:center;margin-top:24px;">
            <a href="http://127.0.0.1:8050/planning"
               style="background:#d97706;color:#ffffff;padding:12px 28px;
                      border-radius:8px;text-decoration:none;font-weight:700;
                      font-size:0.875rem;display:inline-block;">
                Voir les modifications
            </a>
        </div>
    """
    html = base_template(f"Planning modifié — {classe}", contenu, "#d97706")
    return send_email(to, f"Planning semaine {semaine} — {classe} modifié", html)


def email_planning_prof(
    to: str,
    nom_prof: str,
    classe: str,
    semaine: str,
    seances_prof: list
) -> tuple[bool, str]:
    """
    Email envoyé à chaque enseignant concerné quand un planning est validé.
    seances_prof : liste de dicts filtrée sur cet enseignant uniquement.
    """
    nb = len(seances_prof)

    tableau = _tableau_seances_html(
        seances_prof,
        couleur=VERT,
        colonnes=["jour", "date", "module", "heure_debut", "heure_fin"]
    )

    contenu = f"""
        <p style="color:#374151;font-size:0.9rem;line-height:1.6;margin:0 0 16px;">
            Bonjour <strong>{nom_prof}</strong>,
        </p>
        <p style="color:#374151;font-size:0.9rem;line-height:1.6;margin:0 0 20px;">
            Le planning de la classe <strong>{classe}</strong> pour la semaine du
            <strong>{semaine}</strong> vient d'être
            <strong style="color:{VERT};">validé</strong>.
            Vous avez <strong>{nb} séance{'s' if nb > 1 else ''}</strong>
            programmée{'s' if nb > 1 else ''} cette semaine :
        </p>
        {tableau}
        <p style="color:#6b7280;font-size:0.82rem;margin:0 0 20px;">
            Merci de vous connecter sur <strong>{APP_NAME}</strong> pour consulter
            le planning complet.
        </p>
        <div style="text-align:center;margin-top:20px;">
            <a href="http://127.0.0.1:8050/planning"
               style="background:{VERT};color:#ffffff;padding:12px 28px;
                      border-radius:8px;text-decoration:none;font-weight:700;
                      font-size:0.875rem;display:inline-block;">
                Voir le planning
            </a>
        </div>
    """
    html = base_template(f"Vos cours — semaine du {semaine}", contenu, VERT)
    return send_email(to, f"Vos cours semaine {semaine} — {classe}", html)


def email_planning_confirmation_rc(
    to: str,
    nom_rc: str,
    classe: str,
    semaine: str,
    seances: list = None
) -> tuple[bool, str]:
    """
    Email de confirmation envoyé au responsable de classe
    après qu'il a soumis son planning.
    """
    seances = seances or []

    tableau = _tableau_seances_html(
        seances,
        couleur=BLEU,
        colonnes=["jour", "date", "module", "heure_debut", "heure_fin"]
    ) if seances else ""

    contenu = f"""
        <p style="color:#374151;font-size:0.9rem;line-height:1.6;margin:0 0 16px;">
            Bonjour <strong>{nom_rc}</strong>,
        </p>
        <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;
                    padding:16px;margin-bottom:20px;">
            <p style="color:{BLEU};font-weight:700;font-size:0.9rem;margin:0 0 6px;">
                📋 Planning soumis avec succès
            </p>
            <p style="color:#374151;font-size:0.875rem;margin:0;">
                Votre planning pour la classe <strong>{classe}</strong>
                — semaine du <strong>{semaine}</strong> —
                a bien été soumis au responsable de filière pour validation.
                Vous recevrez une notification dès qu'il aura été traité.
            </p>
        </div>
        {f'<p style="color:#374151;font-size:0.85rem;font-weight:700;margin:0 0 8px;">Récapitulatif des séances soumises :</p>' if seances else ""}
        {tableau}
        <div style="text-align:center;margin-top:24px;">
            <a href="http://127.0.0.1:8050/planning"
               style="background:{BLEU};color:#ffffff;padding:12px 28px;
                      border-radius:8px;text-decoration:none;font-weight:700;
                      font-size:0.875rem;display:inline-block;">
                Voir mon planning
            </a>
        </div>
    """
    html = base_template(f"Planning soumis — {classe}", contenu, BLEU)
    return send_email(to, f"Planning semaine {semaine} — {classe} soumis ✅", html)


# ============================================================
#  EMAIL BIENVENUE ETUDIANT  ← NOUVEAU
# ============================================================

def email_bienvenue_etudiant(
    to: str,
    prenom: str,
    nom: str,
    email_connexion: str,
    mot_de_passe: str,
    classe: str,
) -> tuple[bool, str]:
    """
    Email de bienvenue envoyé à chaque étudiant lors de son import en base.

    Contient :
      - Ses identifiants de connexion (email + mot de passe)
      - Le nom de sa classe
      - Un bouton de connexion vers l'application
      - Une recommandation de changer le mot de passe après la première connexion

    Appelé par utils/migration.py → migrate_etudiants() après chaque création.
    """
    contenu = f"""
        <p style="color:#374151;font-size:0.9rem;line-height:1.6;margin:0 0 20px;">
            Bonjour <strong>{prenom} {nom.upper()}</strong>,
        </p>

        <p style="color:#374151;font-size:0.9rem;line-height:1.6;margin:0 0 20px;">
            Bienvenue à l'<strong>ENSAE Dakar</strong> !
            Votre compte sur la plateforme <strong>{APP_NAME}</strong> a été créé.
            Vous pouvez dès maintenant vous connecter pour consulter votre planning,
            vos notes et vos bulletins.
        </p>

        <!-- Encadré identifiants -->
        <table width="100%" cellpadding="0" cellspacing="0"
               style="background:#f0f9ff;border:1.5px solid #bae6fd;
                      border-radius:10px;margin-bottom:24px;">
            <tr>
                <td style="padding:20px 24px;">
                    <p style="color:{BLEU};font-weight:700;font-size:0.95rem;
                               margin:0 0 14px;">
                        🔑 Vos identifiants de connexion
                    </p>

                    <!-- Classe -->
                    <table width="100%" cellpadding="0" cellspacing="0"
                           style="margin-bottom:10px;">
                        <tr>
                            <td style="width:140px;color:#6b7280;font-size:0.82rem;
                                       font-weight:600;padding:4px 0;">
                                Classe :
                            </td>
                            <td style="color:#374151;font-size:0.875rem;
                                       font-weight:500;padding:4px 0;">
                                {classe}
                            </td>
                        </tr>
                    </table>

                    <!-- Email -->
                    <table width="100%" cellpadding="0" cellspacing="0"
                           style="margin-bottom:10px;">
                        <tr>
                            <td style="width:140px;color:#6b7280;font-size:0.82rem;
                                       font-weight:600;padding:4px 0;">
                                Identifiant (email) :
                            </td>
                            <td style="padding:4px 0;">
                                <span style="background:#e0f2fe;color:{BLEU};
                                             font-weight:700;font-size:0.875rem;
                                             padding:3px 10px;border-radius:6px;
                                             font-family:monospace;">
                                    {email_connexion}
                                </span>
                            </td>
                        </tr>
                    </table>

                    <!-- Mot de passe -->
                    <table width="100%" cellpadding="0" cellspacing="0">
                        <tr>
                            <td style="width:140px;color:#6b7280;font-size:0.82rem;
                                       font-weight:600;padding:4px 0;">
                                Mot de passe :
                            </td>
                            <td style="padding:4px 0;">
                                <span style="background:#fef9c3;color:#92400e;
                                             font-weight:700;font-size:0.875rem;
                                             padding:3px 10px;border-radius:6px;
                                             font-family:monospace;">
                                    {mot_de_passe}
                                </span>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>

        <!-- Avertissement sécurité -->
        <table width="100%" cellpadding="0" cellspacing="0"
               style="background:#fffbeb;border:1px solid #fde68a;
                      border-radius:8px;margin-bottom:24px;">
            <tr>
                <td style="padding:14px 18px;">
                    <p style="color:#92400e;font-size:0.82rem;margin:0;">
                        ⚠️ <strong>Conseil de sécurité :</strong>
                        Changez votre mot de passe dès votre première connexion
                        via la page <em>Mon profil</em> de l'application.
                        Ne communiquez jamais vos identifiants à un tiers.
                    </p>
                </td>
            </tr>
        </table>

        <!-- Bouton connexion -->
        <div style="text-align:center;margin-top:8px;">
            <a href="http://127.0.0.1:8050/login"
               style="background:{BLEU};color:#ffffff;padding:13px 32px;
                      border-radius:8px;text-decoration:none;font-weight:700;
                      font-size:0.9rem;display:inline-block;letter-spacing:0.3px;">
                Se connecter à {APP_NAME}
            </a>
        </div>

        <p style="color:#9ca3af;font-size:0.75rem;margin:24px 0 0;text-align:center;">
            En cas de problème de connexion, contactez l'administration de l'ENSAE.
        </p>
    """

    html = base_template(
        f"Bienvenue sur {APP_NAME} — {classe}",
        contenu,
        BLEU
    )
    return send_email(
        to,
        f"Vos identifiants de connexion — {APP_NAME}",
        html
    )


# ============================================================
#  EMAIL BULLETIN
# ============================================================

def email_bulletin(
    to: str,
    nom_etudiant: str,
    prenom_etudiant: str,
    classe: str,
    periode: str,
    moyenne: float,
    rang: int,
    taux_assiduite: float
) -> tuple[bool, str]:
    """Email envoyé à l'étudiant avec ses résultats."""
    mention = (
        "Tres Bien"  if moyenne >= 16 else
        "Bien"       if moyenne >= 14 else
        "Assez Bien" if moyenne >= 12 else
        "Passable"   if moyenne >= 10 else
        "Insuffisant"
    )
    couleur_moy = VERT if moyenne >= 10 else "#ef4444"

    contenu = f"""
        <p style="color:#374151;font-size:0.9rem;line-height:1.6;margin:0 0 16px;">
            Bonjour <strong>{prenom_etudiant} {nom_etudiant}</strong>,
        </p>
        <p style="color:#374151;font-size:0.9rem;margin:0 0 20px;">
            Vos résultats pour la période <strong>{periode}</strong>
            sont disponibles.
        </p>
        <table width="100%" cellpadding="0" cellspacing="0"
               style="border:1px solid #e5e7eb;border-radius:8px;
                      overflow:hidden;margin-bottom:24px;border-collapse:collapse;">
            <tr style="background:{BLEU}12;">
                <th style="padding:10px;font-size:0.72rem;color:{BLEU};
                            text-align:left;font-weight:700;text-transform:uppercase;
                            border-bottom:1px solid #e5e7eb;">Indicateur</th>
                <th style="padding:10px;font-size:0.72rem;color:{BLEU};
                            text-align:left;font-weight:700;text-transform:uppercase;
                            border-bottom:1px solid #e5e7eb;">Valeur</th>
            </tr>
            <tr style="border-bottom:1px solid #f3f4f6;">
                <td style="padding:10px;font-size:0.82rem;color:#6b7280;">Classe</td>
                <td style="padding:10px;font-size:0.82rem;color:#374151;font-weight:500;">{classe}</td>
            </tr>
            <tr style="border-bottom:1px solid #f3f4f6;">
                <td style="padding:10px;font-size:0.82rem;color:#6b7280;">Moyenne générale</td>
                <td style="padding:10px;font-size:0.88rem;color:{couleur_moy};
                            font-weight:700;">{moyenne:.2f} / 20</td>
            </tr>
            <tr style="border-bottom:1px solid #f3f4f6;">
                <td style="padding:10px;font-size:0.82rem;color:#6b7280;">Rang</td>
                <td style="padding:10px;font-size:0.82rem;color:#374151;font-weight:500;">{rang}</td>
            </tr>
            <tr>
                <td style="padding:10px;font-size:0.82rem;color:#6b7280;">Assiduité</td>
                <td style="padding:10px;font-size:0.82rem;color:#374151;font-weight:500;">{taux_assiduite:.1f} %</td>
            </tr>
        </table>
        <div style="text-align:center;margin-bottom:20px;">
            <span style="background:{couleur_moy}15;color:{couleur_moy};
                         padding:6px 18px;border-radius:999px;
                         font-weight:700;font-size:0.82rem;">
                Mention : {mention}
            </span>
        </div>

        <div style="text-align:center;margin-top:24px;">
            <a href="http://127.0.0.1:8050/bulletins"
               style="background:{BLEU};color:#ffffff;padding:12px 28px;
                      border-radius:8px;text-decoration:none;font-weight:700;
                      font-size:0.875rem;display:inline-block;">
                Voir mon bulletin complet
            </a>
        </div>
    """
    html = base_template(f"Vos résultats — {periode}", contenu, BLEU)
    return send_email(to, f"Résultats {periode} — {classe}", html)


# ============================================================
#  TEST
# ============================================================

if __name__ == "__main__":
    print("Test envoi email...")
    ok, err = send_email(
        MAIL_ADDRESS,
        "Test SGA ENSAE",
        base_template(
            "Test de configuration",
            "<p style='color:#374151;'>La configuration email fonctionne correctement.</p>"
        )
    )
    if ok:
        print("[OK] Email envoye avec succes !")
    else:
        print(f"[ERREUR] {err}")