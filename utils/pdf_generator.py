# ============================================================
#  SGA ENSAE — utils/pdf_generator.py
#  Bulletin PDF format officiel ENSAE Dakar
#  Python 3.11 · ReportLab 4.2.0
# ============================================================

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, Image
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas as rl_canvas
from database import SessionLocal
from models import Etudiant, Note, Presence, Module, UE, Classe, Periode

# ============================================================
#  COULEURS
# ============================================================

BLEU_ENSAE   = colors.HexColor("#003580")
VERT_ENSAE   = colors.HexColor("#006B3F")
OR_ENSAE     = colors.HexColor("#F5A623")
GRIS_HEADER  = colors.HexColor("#404040")   # bandeau "BULLETIN DE NOTES"
GRIS_UE      = colors.HexColor("#C0C0C0")   # ligne UE
GRIS_SEM     = colors.HexColor("#808080")   # ligne MOYENNE SEMESTRE
GRIS_ANNUEL  = colors.HexColor("#404040")   # ligne MOYENNE ANNUELLE
BLANC        = colors.white
NOIR         = colors.black
GRIS_CLAIR   = colors.HexColor("#F2F2F2")   # lignes alternees


# ============================================================
#  UTILITAIRES
# ============================================================

def get_mention(moy):
    if moy is None: return "-"
    if moy >= 16:   return "Tres bien"
    if moy >= 14:   return "Bien"
    if moy >= 12:   return "Assez Bien"
    if moy >= 10:   return "Passable"
    return "Insuffisant"

def fmt(val):
    if val is None: return "-"
    return f"{val:.2f}"

def style_cell(text, font="Helvetica", size=8, color=NOIR,
               align=TA_LEFT, bold=False):
    fn = "Helvetica-Bold" if bold else font
    return Paragraph(f"<font name='{fn}' size='{size}'>{text}</font>",
                     ParagraphStyle("_", fontName=fn, fontSize=size,
                                    textColor=color, alignment=align,
                                    leading=size + 2))

def sc(t, **kw): return style_cell(t, **kw)


# ============================================================
#  CANVAS PERSONNALISE (pas de header/footer automatique)
# ============================================================

class SimpleCanvas(rl_canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        nb = len(self._saved)
        for i, state in enumerate(self._saved):
            self.__dict__.update(state)
            # Numero de page en bas
            self.setFont("Helvetica", 7)
            self.setFillColor(colors.HexColor("#9ca3af"))
            self.drawCentredString(
                A4[0] / 2, 0.5*cm,
                f"Page {i+1} / {nb} — SGA ENSAE — Document confidentiel"
            )
            rl_canvas.Canvas.showPage(self)
        rl_canvas.Canvas.save(self)


# ============================================================
#  GENERATION BULLETIN
# ============================================================

def generate_bulletin(etudiant_id: int,
                      periode_label: str = "2024-2025",
                      annee_academique: str = "2024-2025") -> bytes:

    db = SessionLocal()
    try:
        e = db.query(Etudiant).filter(Etudiant.id == etudiant_id).first()
        if not e:
            raise ValueError(f"Etudiant {etudiant_id} introuvable.")

        nom        = e.user.nom    if e.user else "-"
        prenom     = e.user.prenom if e.user else "-"
        email      = e.user.email  if e.user else "-"
        matricule  = e.matricule
        classe_nom = e.classe.nom              if e.classe else "-"
        filiere    = e.classe.filiere.libelle  if e.classe and e.classe.filiere else "-"
        naissance  = e.date_naissance.strftime("%d/%m/%Y") if e.date_naissance else "-"
        annee_ins  = e.annee_scolaire or "-"

        # Modules groupes par periode puis UE
        modules    = db.query(Module).filter(Module.classe_id == e.classe_id).all()
        all_notes  = db.query(Note).filter(Note.etudiant_id == e.id).all()

        # Periodes
        periodes_ids = sorted(set(m.ue.periode_id for m in modules if m.ue and m.ue.periode_id))
        periodes_map = {}
        for pid in periodes_ids:
            p = db.query(Periode).filter(Periode.id == pid).first()
            if p:
                periodes_map[pid] = p.libelle

        # Organiser : periode -> ue -> modules
        data_tree = {}
        for m in modules:
            pid    = m.ue.periode_id if m.ue else 0
            ue_lib = m.ue.libelle    if m.ue else "Sans UE"
            ue_coef = m.ue.coefficient if m.ue else 1

            if pid not in data_tree:
                data_tree[pid] = {}
            if ue_lib not in data_tree[pid]:
                data_tree[pid][ue_lib] = {"coef": ue_coef, "modules": []}

            notes_m = [n for n in all_notes if n.module_id == m.id]
            note1   = next((n.note for n in notes_m if n.numero == 1), None)
            note2   = next((n.note for n in notes_m if n.numero == 2), None)
            if note1 is not None and note2 is not None:
                moy_mod = round((note1 + note2) / 2, 2)
            elif note1 is not None:
                moy_mod = note1
            elif note2 is not None:
                moy_mod = note2
            else:
                moy_mod = None

            data_tree[pid][ue_lib]["modules"].append({
                "libelle" : m.libelle,
                "coef"    : m.coefficient,
                "note1"   : note1,
                "note2"   : note2,
                "moy"     : moy_mod,
            })

        # Calculer moyennes UE et semestres
        moy_semestres = {}
        total_credits_annuel = 0
        total_pts_annuel     = 0

        for pid, ues in data_tree.items():
            total_pts_sem  = 0
            total_cred_sem = 0
            for ue_lib, ue_data in ues.items():
                mods_avec = [m for m in ue_data["modules"] if m["moy"] is not None]
                if mods_avec:
                    s  = sum(m["moy"] * m["coef"] for m in mods_avec)
                    sc_val = sum(m["coef"] for m in mods_avec)
                    ue_data["moy_ue"] = round(s / sc_val, 2) if sc_val > 0 else None
                    total_pts_sem  += (ue_data["moy_ue"] or 0) * ue_data["coef"]
                    total_cred_sem += ue_data["coef"]
                else:
                    ue_data["moy_ue"] = None

            total_credits_annuel += total_cred_sem
            total_pts_annuel     += total_pts_sem
            moy_sem = round(total_pts_sem / total_cred_sem, 2) if total_cred_sem > 0 else None
            moy_semestres[pid] = {"moy": moy_sem, "credits": total_cred_sem}

        moy_annuelle = round(total_pts_annuel / total_credits_annuel, 2) \
            if total_credits_annuel > 0 else None

        # Assiduite
        total_s  = db.query(Presence).filter(Presence.etudiant_id == e.id).count()
        presents = db.query(Presence).filter(
            Presence.etudiant_id == e.id, Presence.present == True
        ).count()
        nb_absences = total_s - presents

    finally:
        db.close()

    # ── Construction PDF ──────────────────────────────────────
    buffer   = io.BytesIO()
    logo_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "assets", "img", "logo_ensae.png"
    )

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=1.5*cm, bottomMargin=1.2*cm,
        leftMargin=1.2*cm, rightMargin=1.2*cm
    )

    story = []
    W     = A4[0] - 2.4*cm   # largeur utile

    # ── HEADER ────────────────────────────────────────────────
    # Logo + titre ecole
    header_rows = []
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=2*cm, height=2*cm)
    else:
        logo = sc("ENSAE", bold=True, size=14, align=TA_CENTER)

    header_rows = [[
        logo,
        sc("Ecole Nationale de la Statistique et de l'Analyse Economique Pierre NDIAYE\n"
           "(ENSAE de Dakar)",
           bold=True, size=10, align=TA_CENTER),
        sc(f"Annee academique\n{annee_academique}",
           size=8, align=TA_RIGHT)
    ]]
    t_header = Table(header_rows, colWidths=[2.5*cm, 11*cm, 3.5*cm])
    t_header.setStyle(TableStyle([
        ("VALIGN",  (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",   (1,0), (1,0),   "CENTER"),
        ("ALIGN",   (2,0), (2,0),   "RIGHT"),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(t_header)
    story.append(Spacer(1, 0.2*cm))

    # Bandeau BULLETIN DE NOTES
    bandeau = Table([[
        sc("BULLETIN DE NOTES", bold=True, size=11,
           color=BLANC, align=TA_CENTER)
    ]], colWidths=[W])
    bandeau.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), GRIS_HEADER),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(bandeau)
    story.append(Spacer(1, 0.15*cm))

    # Filiere
    filiere_table = Table([[
        sc(filiere.upper(),          bold=True, size=10, align=TA_CENTER),
    ], [
        sc(f"({classe_nom})",        bold=True, size=9,  align=TA_CENTER),
    ]], colWidths=[W])
    filiere_table.setStyle(TableStyle([
        ("TOPPADDING",    (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
    ]))
    story.append(filiere_table)
    story.append(Spacer(1, 0.2*cm))

    # ── INFOS ETUDIANT ────────────────────────────────────────
    lw = 4*cm
    vw = 8*cm
    info_data = [
        [sc("NOMS",               bold=True, size=8), sc(nom.upper(),  size=8, bold=True)],
        [sc("Prenoms",            bold=True, size=8), sc(prenom,       size=8)],
        [sc("Date de naissance",  bold=True, size=8), sc(naissance,    size=8)],
        [sc("Matricule",          bold=True, size=8), sc(matricule,    size=8)],
        [sc("Premiere Inscription", bold=True, size=8), sc(annee_ins,  size=8)],
    ]
    t_info = Table(info_data, colWidths=[lw, vw])
    t_info.setStyle(TableStyle([
        ("ALIGN",         (0,0), (0,-1), "RIGHT"),
        ("ALIGN",         (1,0), (1,-1), "LEFT"),
        ("TOPPADDING",    (0,0), (-1,-1), 2),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
        ("LEFTPADDING",   (0,0), (0,-1), 4),
        ("LEFTPADDING",   (1,0), (1,-1), 12),
    ]))

    # Centrer le tableau infos
    outer = Table([[t_info]], colWidths=[W])
    outer.setStyle(TableStyle([("ALIGN", (0,0), (-1,-1), "CENTER")]))
    story.append(outer)
    story.append(Spacer(1, 0.3*cm))

    # ── COLONNES EN-TETE NOTES ────────────────────────────────
    cw = [7.5*cm, 1.8*cm, 1.8*cm, 1.8*cm, 2*cm, 2.1*cm]

    def row_entete():
        return [
            sc("",            bold=True, size=8),
            sc("Note 1",      bold=True, size=8, align=TA_CENTER),
            sc("Note 2",      bold=True, size=8, align=TA_CENTER),
            sc("Credits",     bold=True, size=8, align=TA_CENTER),
            sc("Moyenne",     bold=True, size=8, align=TA_CENTER),
            sc("Appreciation",bold=True, size=8, align=TA_CENTER),
        ]

    def row_ue(ue_lib, moy_ue):
        return [
            sc(ue_lib.upper(), bold=True, size=8, color=BLANC),
            sc("", size=8),
            sc("", size=8),
            sc("Validee" if moy_ue and moy_ue >= 10 else "",
               size=7, color=BLANC, align=TA_CENTER, bold=True),
            sc("", size=8),
            sc("", size=8),
        ]

    def row_module(m, idx):
        moy_col = colors.HexColor("#006B3F") if m["moy"] and m["moy"] >= 10 \
                  else colors.HexColor("#CC0000") if m["moy"] is not None \
                  else NOIR
        return [
            sc(m["libelle"],          size=8),
            sc(fmt(m["note1"]),       size=8, align=TA_CENTER),
            sc(fmt(m["note2"]),       size=8, align=TA_CENTER),
            sc(str(m["coef"]),        size=8, align=TA_CENTER),
            sc(fmt(m["moy"]),         size=8, align=TA_CENTER, color=moy_col, bold=True),
            sc(get_mention(m["moy"]), size=8, align=TA_CENTER, color=moy_col),
        ]

    def row_moy_sem(label, credits, moy):
        moy_col = BLANC
        return [
            sc(label,          bold=True, size=9, color=BLANC),
            sc("",             size=8),
            sc("",             size=8),
            sc(str(credits),   bold=True, size=9, color=BLANC, align=TA_CENTER),
            sc(fmt(moy),       bold=True, size=10, color=BLANC, align=TA_CENTER),
            sc(get_mention(moy), bold=True, size=9, color=BLANC, align=TA_CENTER),
        ]

    # ── TABLEAU NOTES PAR SEMESTRE ────────────────────────────
    for pid in sorted(data_tree.keys()):
        ues      = data_tree[pid]
        sem_lib  = periodes_map.get(pid, f"Semestre {pid}")
        sem_data = moy_semestres.get(pid, {"moy": None, "credits": 0})

        # Bandeau semestre
        sem_band = Table([[
            sc(sem_lib.upper(), bold=True, size=9, color=BLANC, align=TA_CENTER)
        ]], colWidths=[W])
        sem_band.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), BLEU_ENSAE),
            ("TOPPADDING",    (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(sem_band)

        # En-tete colonnes
        all_rows  = [row_entete()]
        row_styles = [
            # En-tete
            ("BACKGROUND",    (0,0), (-1,0), colors.HexColor("#E0E0E0")),
            ("TEXTCOLOR",     (0,0), (-1,0), NOIR),
            ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ]

        row_idx = 1
        for ue_lib, ue_data in ues.items():
            # Ligne UE
            all_rows.append(row_ue(ue_lib, ue_data.get("moy_ue")))
            row_styles += [
                ("BACKGROUND",  (0, row_idx), (-1, row_idx), GRIS_UE),
                ("SPAN",        (0, row_idx), (1,  row_idx)),
            ]
            row_idx += 1

            # Modules
            for i, m in enumerate(ue_data["modules"]):
                all_rows.append(row_module(m, i))
                bg = GRIS_CLAIR if i % 2 == 0 else BLANC
                row_styles.append(("BACKGROUND", (0, row_idx), (-1, row_idx), bg))
                row_idx += 1

        # Ligne MOYENNE SEMESTRE
        all_rows.append(row_moy_sem(
            f"MOYENNE {sem_lib.upper()}",
            sem_data["credits"],
            sem_data["moy"]
        ))
        row_styles += [
            ("BACKGROUND", (0, row_idx), (-1, row_idx), GRIS_SEM),
            ("FONTNAME",   (0, row_idx), (-1, row_idx), "Helvetica-Bold"),
        ]

        t_notes = Table(all_rows, colWidths=cw)
        base_style = [
            ("BOX",          (0,0),  (-1,-1), 0.5, colors.HexColor("#AAAAAA")),
            ("INNERGRID",    (0,0),  (-1,-1), 0.3, colors.HexColor("#CCCCCC")),
            ("VALIGN",       (0,0),  (-1,-1), "MIDDLE"),
            ("TOPPADDING",   (0,0),  (-1,-1), 3),
            ("BOTTOMPADDING",(0,0),  (-1,-1), 3),
            ("LEFTPADDING",  (0,0),  (-1,-1), 4),
            ("RIGHTPADDING", (0,0),  (-1,-1), 4),
        ]
        t_notes.setStyle(TableStyle(base_style + row_styles))
        story.append(t_notes)
        story.append(Spacer(1, 0.3*cm))

    # ── SECTION ABSENCES ─────────────────────────────────────
    abs_data = [[
        sc("Heures d'absence non justifiees :", bold=True, size=8),
        sc(str(nb_absences), size=8, bold=True),
        sc("Penalite appliquee :", bold=True, size=8),
        sc("0", size=8),
    ]]
    t_abs = Table(abs_data, colWidths=[6*cm, 2*cm, 5*cm, 2*cm])
    t_abs.setStyle(TableStyle([
        ("TOPPADDING",    (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("LEFTPADDING",   (0,0), (-1,-1), 4),
    ]))
    story.append(t_abs)
    story.append(Spacer(1, 0.15*cm))

    # ── MOYENNE ANNUELLE ─────────────────────────────────────
    annuel_rows = [[
        sc("MOYENNE ANNUELLE", bold=True, size=10, color=BLANC),
        sc("", size=8),
        sc("", size=8),
        sc(str(total_credits_annuel), bold=True, size=10,
           color=BLANC, align=TA_CENTER),
        sc(fmt(moy_annuelle), bold=True, size=12,
           color=BLANC, align=TA_CENTER),
        sc(get_mention(moy_annuelle), bold=True, size=10,
           color=BLANC, align=TA_CENTER),
    ]]
    t_annuel = Table(annuel_rows, colWidths=cw)
    t_annuel.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), GRIS_ANNUEL),
        ("BOX",           (0,0), (-1,-1), 1, NOIR),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 4),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(t_annuel)
    story.append(Spacer(1, 0.3*cm))

    # ── CLASSEMENT + DECISION ────────────────────────────────
    decision = "Admis(e) en deuxieme annee" if moy_annuelle and moy_annuelle >= 10 \
               else "Ajourné(e) — Session de rattrapage"

    class_data = [[
        sc("Classement general :", bold=True, size=8),
        sc("- / -",               size=8),
        sc("Decision du Jury :",  bold=True, size=8),
        sc(decision,              size=8, bold=True,
           color=VERT_ENSAE if moy_annuelle and moy_annuelle >= 10
           else colors.HexColor("#CC0000")),
    ]]
    t_class = Table(class_data, colWidths=[4*cm, 3*cm, 4*cm, 6*cm])
    t_class.setStyle(TableStyle([
        ("TOPPADDING",    (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("LEFTPADDING",   (0,0), (-1,-1), 4),
        ("BOX",           (0,0), (-1,-1), 0.5, colors.HexColor("#AAAAAA")),
        ("BACKGROUND",    (0,0), (-1,-1), GRIS_CLAIR),
    ]))
    story.append(t_class)
    story.append(Spacer(1, 0.5*cm))

    # ── SIGNATURES ───────────────────────────────────────────
    sig_data = [[
        sc("Le Directeur des Etudes", bold=True, size=8, align=TA_CENTER),
        sc("",                        size=8),
        sc("Cachet et Signature",     bold=True, size=8, align=TA_CENTER),
    ]]
    t_sig = Table(sig_data, colWidths=[6*cm, 5*cm, 6*cm])
    t_sig.setStyle(TableStyle([
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING",    (0,0), (-1,-1), 24),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(t_sig)

    # ── BUILD ─────────────────────────────────────────────────
    doc.build(story, canvasmaker=SimpleCanvas)
    buffer.seek(0)
    return buffer.read()


# ============================================================
#  TEST STANDALONE
# ============================================================

if __name__ == "__main__":
    db = SessionLocal()
    try:
        e = db.query(Etudiant).first()
        if not e:
            print("Aucun etudiant en base.")
        else:
            pdf = generate_bulletin(e.id)
            out = f"bulletin_{e.matricule}.pdf"
            with open(out, "wb") as f:
                f.write(pdf)
            print(f"[OK] Bulletin genere : {out}")
    finally:
        db.close()