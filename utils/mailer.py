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
    Email envoye au responsable de filiere quand un planning est soumis.
    seances : liste de dicts {module, date, heure_debut, heure_fin}
    """
    rows_seances = "".join([
        f"""
        <tr style="border-bottom:1px solid #f3f4f6;">
            <td style="padding:8px 12px;font-size:0.82rem;color:#374151;">
                {s.get('date', '-')}
            </td>
            <td style="padding:8px 12px;font-size:0.82rem;color:#374151;">
                {s.get('module', '-')}
            </td>
            <td style="padding:8px 12px;font-size:0.82rem;color:#6b7280;">
                {s.get('heure_debut', '-')} - {s.get('heure_fin', '-')}
            </td>
        </tr>
        """
        for s in seances
    ])

    contenu = f"""
        <p style="color:#374151;font-size:0.9rem;line-height:1.6;margin:0 0 16px;">
            Bonjour <strong>{nom_resp_filiere}</strong>,
        </p>
        <p style="color:#374151;font-size:0.9rem;line-height:1.6;margin:0 0 20px;">
            <strong>{nom_resp_classe}</strong> a soumis un planning pour la classe
            <strong>{classe}</strong> — semaine du <strong>{semaine}</strong>.
        </p>

        <!-- Tableau seances -->
        <table width="100%" cellpadding="0" cellspacing="0"
               style="border:1px solid #e5e7eb;border-radius:8px;
                      overflow:hidden;margin-bottom:24px;">
            <tr style="background:{BLEU}10;">
                <th style="padding:10px 12px;font-size:0.75rem;color:{BLEU};
                           text-align:left;font-weight:700;text-transform:uppercase;">
                    Date
                </th>
                <th style="padding:10px 12px;font-size:0.75rem;color:{BLEU};
                           text-align:left;font-weight:700;text-transform:uppercase;">
                    Module
                </th>
                <th style="padding:10px 12px;font-size:0.75rem;color:{BLEU};
                           text-align:left;font-weight:700;text-transform:uppercase;">
                    Horaire
                </th>
            </tr>
            {rows_seances}
        </table>

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

    html = base_template(
        f"Nouveau planning a valider — {classe}",
        contenu,
        BLEU
    )
    return send_email(to, f"Planning semaine {semaine} — {classe} en attente de validation", html)


def email_planning_valide(
    to: str,
    nom_resp_classe: str,
    classe: str,
    semaine: str
) -> tuple[bool, str]:
    """Email envoye au responsable de classe quand son planning est valide."""
    contenu = f"""
        <p style="color:#374151;font-size:0.9rem;line-height:1.6;margin:0 0 16px;">
            Bonjour <strong>{nom_resp_classe}</strong>,
        </p>
        <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;
                    padding:16px;margin-bottom:20px;">
            <p style="color:{VERT};font-weight:700;font-size:0.9rem;margin:0 0 6px;">
                Planning valide
            </p>
            <p style="color:#374151;font-size:0.875rem;margin:0;">
                Votre planning de la classe <strong>{classe}</strong>
                pour la semaine du <strong>{semaine}</strong>
                a ete <strong style="color:{VERT};">valide</strong>.
            </p>
        </div>
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
    return send_email(to, f"Planning semaine {semaine} — {classe} valide", html)


def email_planning_rejete(
    to: str,
    nom_resp_classe: str,
    classe: str,
    semaine: str,
    commentaire: str
) -> tuple[bool, str]:
    """Email envoye au responsable de classe quand son planning est rejete."""
    contenu = f"""
        <p style="color:#374151;font-size:0.9rem;line-height:1.6;margin:0 0 16px;">
            Bonjour <strong>{nom_resp_classe}</strong>,
        </p>
        <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:8px;
                    padding:16px;margin-bottom:20px;">
            <p style="color:#ef4444;font-weight:700;font-size:0.9rem;margin:0 0 6px;">
                Planning rejete
            </p>
            <p style="color:#374151;font-size:0.875rem;margin:0 0 10px;">
                Votre planning de la classe <strong>{classe}</strong>
                pour la semaine du <strong>{semaine}</strong>
                a ete <strong style="color:#ef4444;">rejete</strong>.
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
    html = base_template(f"Planning rejete — {classe}", contenu, "#ef4444")
    return send_email(to, f"Planning semaine {semaine} — {classe} rejete", html)


def email_planning_modifie(
    to: str,
    nom_resp_classe: str,
    classe: str,
    semaine: str,
    commentaire: str
) -> tuple[bool, str]:
    """Email envoye au responsable de classe quand son planning est modifie."""
    contenu = f"""
        <p style="color:#374151;font-size:0.9rem;line-height:1.6;margin:0 0 16px;">
            Bonjour <strong>{nom_resp_classe}</strong>,
        </p>
        <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:8px;
                    padding:16px;margin-bottom:20px;">
            <p style="color:#d97706;font-weight:700;font-size:0.9rem;margin:0 0 6px;">
                Planning modifie
            </p>
            <p style="color:#374151;font-size:0.875rem;margin:0 0 10px;">
                Votre planning de la classe <strong>{classe}</strong>
                pour la semaine du <strong>{semaine}</strong>
                a ete <strong style="color:#d97706;">modifie</strong>.
            </p>
            <p style="color:#374151;font-size:0.875rem;margin:0;">
                <strong>Commentaire :</strong> {commentaire or "Aucun commentaire."}
            </p>
        </div>
        <div style="text-align:center;margin-top:24px;">
            <a href="http://127.0.0.1:8050/planning"
               style="background:{OR};color:{BLEU};padding:12px 28px;
                      border-radius:8px;text-decoration:none;font-weight:700;
                      font-size:0.875rem;display:inline-block;">
                Voir les modifications
            </a>
        </div>
    """
    html = base_template(f"Planning modifie — {classe}", contenu, "#d97706")
    return send_email(to, f"Planning semaine {semaine} — {classe} modifie", html)


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
    """Email envoye a l'etudiant avec ses resultats."""
    mention = (
        "Tres Bien" if moyenne >= 16 else
        "Bien"      if moyenne >= 14 else
        "Assez Bien" if moyenne >= 12 else
        "Passable"  if moyenne >= 10 else
        "Insuffisant"
    )
    couleur_moy = VERT if moyenne >= 10 else "#ef4444"

    contenu = f"""
        <p style="color:#374151;font-size:0.9rem;line-height:1.6;margin:0 0 16px;">
            Bonjour <strong>{prenom_etudiant} {nom_etudiant}</strong>,
        </p>
        <p style="color:#374151;font-size:0.9rem;margin:0 0 20px;">
            Vos resultats pour la periode <strong>{periode}</strong>
            sont disponibles.
        </p>

        <!-- Recap resultats -->
        <table width="100%" cellpadding="0" cellspacing="0"
               style="border:1px solid #e5e7eb;border-radius:8px;
                      overflow:hidden;margin-bottom:24px;">
            <tr style="background:{BLEU}08;">
                <td style="padding:14px 16px;border-bottom:1px solid #e5e7eb;">
                    <span style="color:#9ca3af;font-size:0.72rem;
                                 text-transform:uppercase;font-weight:600;">
                        Classe
                    </span><br>
                    <span style="color:#111827;font-weight:600;font-size:0.9rem;">
                        {classe}
                    </span>
                </td>
                <td style="padding:14px 16px;border-bottom:1px solid #e5e7eb;">
                    <span style="color:#9ca3af;font-size:0.72rem;
                                 text-transform:uppercase;font-weight:600;">
                        Moyenne generale
                    </span><br>
                    <span style="color:{couleur_moy};font-weight:800;font-size:1.2rem;">
                        {moyenne}/20
                    </span>
                </td>
                <td style="padding:14px 16px;border-bottom:1px solid #e5e7eb;">
                    <span style="color:#9ca3af;font-size:0.72rem;
                                 text-transform:uppercase;font-weight:600;">
                        Rang
                    </span><br>
                    <span style="color:{BLEU};font-weight:700;font-size:0.9rem;">
                        {rang}
                    </span>
                </td>
                <td style="padding:14px 16px;border-bottom:1px solid #e5e7eb;">
                    <span style="color:#9ca3af;font-size:0.72rem;
                                 text-transform:uppercase;font-weight:600;">
                        Assiduite
                    </span><br>
                    <span style="color:{VERT if taux_assiduite >= 80 else '#ef4444'};
                                 font-weight:700;font-size:0.9rem;">
                        {taux_assiduite}%
                    </span>
                </td>
            </tr>
            <tr>
                <td colspan="4" style="padding:12px 16px;text-align:center;">
                    <span style="background:{couleur_moy}15;color:{couleur_moy};
                                 padding:4px 16px;border-radius:999px;
                                 font-weight:700;font-size:0.82rem;">
                        Mention : {mention}
                    </span>
                </td>
            </tr>
        </table>

        <div style="text-align:center;margin-top:24px;">
            <a href="http://127.0.0.1:8050/bulletins"
               style="background:{BLEU};color:#ffffff;padding:12px 28px;
                      border-radius:8px;text-decoration:none;font-weight:700;
                      font-size:0.875rem;display:inline-block;">
                Voir mon bulletin complet
            </a>
        </div>
    """
    html = base_template(f"Vos resultats — {periode}", contenu, BLEU)
    return send_email(
        to,
        f"Resultats {periode} — {classe}",
        html
    )


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