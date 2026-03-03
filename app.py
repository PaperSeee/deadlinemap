"""
============================================================
  DeadlineMap - app.py
  Application Flask (Couche Présentation / Routes HTTP)
============================================================

ARCHITECTURE WEB :

Flask suit le pattern MVC (Model-View-Controller) :
  - Model     → models.py (Deadline, Course, Task...)
  - View      → templates/*.html (Jinja2)
  - Controller → app.py (routes Flask = contrôleurs)

Les managers (DeadlineManager, CourseManager) jouent le rôle
de la couche Service/Repository entre Controller et Model.

ROUTES DISPONIBLES :
  GET  /                    → Tableau de bord principal
  GET  /deadlines           → Liste de toutes les deadlines
  GET  /deadlines/new       → Formulaire création
  POST /deadlines/new       → Traitement création
  GET  /deadlines/<id>/edit → Formulaire modification
  POST /deadlines/<id>/edit → Traitement modification
  POST /deadlines/<id>/delete → Suppression
  POST /deadlines/<id>/status → Changement de statut (AJAX)
  GET  /courses             → Liste des cours
  GET  /courses/new         → Formulaire création cours
  POST /courses/new         → Traitement création cours
  POST /courses/<id>/delete → Suppression cours
  GET  /ai-report           → Rapport IA complet
  GET  /api/stats           → API JSON pour les graphiques
"""

import os
from datetime import date, datetime
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, jsonify
)

from models import Deadline, Course, Priority, Status
from manager import DeadlineManager, CourseManager
from ai_advisor import AIAdvisor


# =============================================================
#  Configuration de l'Application Flask
# =============================================================

app = Flask(__name__)
app.secret_key = "ichec-montgomery-anjou-2026-deadlinemap-secret"

# Chemins des fichiers de données
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))

# Sur Vercel, le système de fichiers est en lecture seule sauf /tmp
if os.environ.get("VERCEL"):
    DATA_FILE = "/tmp/deadlinemap.json"
else:
    DATA_FILE = os.path.join(BASE_DIR, "data", "deadlinemap.json")

# Expose la fonction enumerate() de Python dans les templates Jinja2
# (non disponible par défaut dans Jinja2)
app.jinja_env.globals["enumerate"] = enumerate

# ─── Filtre abs (valeur absolue) pour Jinja2 ─────────────────
@app.template_filter("abs")
def abs_filter(value):
    """Retourne la valeur absolue d'un nombre (ex: jours de retard)."""
    return abs(value)

# ─── Filtre min pour Jinja2 ──────────────────────────────────
app.jinja_env.globals["min"] = min
app.jinja_env.globals["max"] = max

# Instanciation des managers (injection de dépendances via constructeur)
deadline_mgr  = DeadlineManager(DATA_FILE)
course_mgr    = CourseManager(DATA_FILE)

# Premier lancement : seed des cours ICHEC si aucun cours n'existe
try:
    if not course_mgr.get_all():
        course_mgr.seed_ichec_courses()
except Exception as _seed_err:
    print(f"[WARN] Seed impossible: {_seed_err}")


# =============================================================
#  Filtres Jinja2 Personnalisés
# =============================================================

@app.template_filter("fr_date")
def fr_date_filter(d) -> str:
    """Formate une date en format français : '15 mars 2026'."""
    if isinstance(d, str):
        d = date.fromisoformat(d)
    months = [
        "", "janvier", "février", "mars", "avril", "mai", "juin",
        "juillet", "août", "septembre", "octobre", "novembre", "décembre"
    ]
    return f"{d.day} {months[d.month]} {d.year}"

@app.template_filter("stress_color")
def stress_color_filter(score: int) -> str:
    """Retourne une couleur HEX basée sur le score de stress (pour les jauges)."""
    if score >= 80:
        return "#FF4757"  # Rouge vif
    elif score >= 60:
        return "#FF6348"  # Orange
    elif score >= 40:
        return "#FFA502"  # Ambre
    elif score >= 20:
        return "#2ED573"  # Vert
    else:
        return "#7BED9F"  # Vert clair


# =============================================================
#  ROUTE : Tableau de Bord Principal
# =============================================================

@app.route("/")
def index():
    """
    Page d'accueil : tableau de bord avec métriques et deadlines urgentes.

    Données transmises au template :
    - stats         : Métriques globales (total, en retard, à venir...)
    - urgent        : Top 5 deadlines les plus urgentes
    - upcoming_7d   : Deadlines dans les 7 prochains jours
    - courses_dict  : Dictionnaire {id: Course} pour les lookups de nom
    """
    stats        = deadline_mgr.get_stats()
    urgent       = deadline_mgr.get_sorted_by_stress()[:5]
    upcoming_7d  = deadline_mgr.get_upcoming(7)
    courses_dict = course_mgr.get_as_dict()

    return render_template(
        "index.html",
        stats       = stats,
        urgent      = urgent,
        upcoming    = upcoming_7d,
        upcoming_7d = upcoming_7d,
        courses     = courses_dict,
        today       = date.today(),
    )


# =============================================================
#  ROUTES : Gestion des Deadlines (CRUD)
# =============================================================

@app.route("/deadlines")
def deadlines_list():
    """
    Liste complète des deadlines avec options de filtrage et tri.
    Paramètres GET : ?sort=stress|date|priority&filter=active|all|overdue&course=<id>
    """
    sort_by    = request.args.get("sort",   "date")
    filter_by  = request.args.get("filter", "active")
    course_id  = request.args.get("course", "")

    # Récupération selon le filtre
    if filter_by == "overdue":
        deadlines = deadline_mgr.get_overdue()
    elif filter_by == "all":
        deadlines = deadline_mgr.get_all()
    else:  # active (défaut)
        deadlines = deadline_mgr.get_active()

    # Filtre par cours (optionnel)
    if course_id:
        deadlines = [dl for dl in deadlines if dl.course_id == course_id]

    # Tri
    if sort_by == "stress":
        deadlines = sorted(deadlines, key=lambda d: d.stress_score, reverse=True)
    elif sort_by == "priority":
        deadlines = sorted(deadlines, key=lambda d: d.priority.value, reverse=True)
    # Par défaut : tri par date (déjà fait par get_all())

    courses_dict = course_mgr.get_as_dict()
    all_courses  = course_mgr.get_all()

    return render_template(
        "deadlines_list.html",
        deadlines   = deadlines,
        courses     = courses_dict,
        all_courses = all_courses,
        sort_by     = sort_by,
        filter_by   = filter_by,
        selected_course = course_id,
    )


@app.route("/deadlines/new", methods=["GET", "POST"])
def deadline_new():
    """
    Formulaire de création d'une nouvelle deadline.

    GET  → Affiche le formulaire vide.
    POST → Valide et crée la deadline, redirige vers la liste.
    """
    all_courses = course_mgr.get_all()

    if request.method == "POST":
        try:
            # Extraction et validation des données du formulaire
            title           = request.form.get("title", "").strip()
            due_date_str    = request.form.get("due_date", "")
            course_id       = request.form.get("course_id", "")
            priority_str    = request.form.get("priority", "MOYEN")
            estimated_hours = float(request.form.get("estimated_hours", 0) or 0)
            description     = request.form.get("description", "").strip()

            # Validation
            if not title:
                flash("Le titre est obligatoire ! (même pour ton TFE)", "error")
                return render_template("deadline_form.html", courses=all_courses, deadline=None)

            if not due_date_str:
                flash("La date limite est obligatoire !", "error")
                return render_template("deadline_form.html", courses=all_courses, deadline=None)

            due_date = date.fromisoformat(due_date_str)

            # Création de l'objet Deadline (POO)
            new_deadline = Deadline(
                title           = title,
                due_date        = due_date,
                course_id       = course_id,
                priority        = Priority.from_string(priority_str),
                status          = Status.A_FAIRE,
                estimated_hours = estimated_hours,
                description     = description,
            )

            deadline_mgr.add(new_deadline)
            flash(f"✅ Deadline '{title}' ajoutée ! Maintenant au boulot...", "success")
            return redirect(url_for("deadlines_list"))

        except ValueError as e:
            flash(f"Erreur de validation : {str(e)}", "error")

    return render_template("deadline_form.html", courses=all_courses, deadline=None, today=date.today())


@app.route("/deadlines/<deadline_id>/edit", methods=["GET", "POST"])
def deadline_edit(deadline_id: str):
    """
    Formulaire de modification d'une deadline existante.

    GET  → Affiche le formulaire pré-rempli avec les données actuelles.
    POST → Valide et met à jour la deadline.
    """
    dl = deadline_mgr.get_by_id(deadline_id)
    if not dl:
        flash("Deadline introuvable. Elle a peut-être déjà été supprimée ?", "error")
        return redirect(url_for("deadlines_list"))

    all_courses = course_mgr.get_all()

    if request.method == "POST":
        try:
            dl.title           = request.form.get("title", dl.title)
            due_date_str       = request.form.get("due_date", "")
            if due_date_str:
                dl.due_date    = date.fromisoformat(due_date_str)
            dl.course_id       = request.form.get("course_id", dl.course_id)
            dl.priority        = Priority.from_string(request.form.get("priority", dl.priority.name))
            dl.status          = Status(request.form.get("status", dl.status.value))
            dl.estimated_hours = float(request.form.get("estimated_hours", dl.estimated_hours) or 0)
            dl.description     = request.form.get("description", dl.description)

            deadline_mgr.update(dl)
            flash(f"✅ '{dl.title}' mise à jour avec succès !", "success")
            return redirect(url_for("deadlines_list"))

        except ValueError as e:
            flash(f"Erreur : {str(e)}", "error")

    return render_template("deadline_form.html", deadline=dl, courses=all_courses, today=date.today())


@app.route("/deadlines/<deadline_id>/delete", methods=["POST"])
def deadline_delete(deadline_id: str):
    """Suppression d'une deadline (via formulaire POST pour sécurité CSRF basique)."""
    dl = deadline_mgr.get_by_id(deadline_id)
    if dl:
        deadline_mgr.delete(deadline_id)
        flash(f"🗑️ '{dl.title}' supprimée. Adieu !", "info")
    else:
        flash("Deadline introuvable.", "error")
    return redirect(url_for("deadlines_list"))


@app.route("/deadlines/<deadline_id>/status", methods=["POST"])
def deadline_status(deadline_id: str):
    """
    Change le statut d'une deadline via AJAX (appelé depuis les boutons rapides).
    Retourne du JSON pour mise à jour sans rechargement de page.
    """
    dl = deadline_mgr.get_by_id(deadline_id)
    if not dl:
        return jsonify({"success": False, "error": "Not found"}), 404

    new_status_str = request.form.get("status") or request.json.get("status", "")
    try:
        dl.status = Status(new_status_str)
        deadline_mgr.update(dl)
        return jsonify({
            "success":     True,
            "new_status":  dl.status.value,
            "status_label": dl.status.label_fr(),
            "stress_score": dl.stress_score,
        })
    except ValueError:
        return jsonify({"success": False, "error": "Invalid status"}), 400


# =============================================================
#  ROUTES : Gestion des Cours
# =============================================================

@app.route("/courses")
def courses_list():
    """Affiche la liste de tous les cours enregistrés."""
    all_courses  = course_mgr.get_all()
    all_deadlines = deadline_mgr.get_all()

    # Calcul du nombre de deadlines par cours
    dl_count_by_course = {}
    for dl in all_deadlines:
        dl_count_by_course[dl.course_id] = dl_count_by_course.get(dl.course_id, 0) + 1

    return render_template(
        "courses_list.html",
        courses          = all_courses,
        dl_count_by_course = dl_count_by_course,
    )


@app.route("/courses/new", methods=["GET", "POST"])
def course_new():
    """Formulaire de création d'un cours."""
    if request.method == "POST":
        try:
            name      = request.form.get("name", "").strip()
            professor = request.form.get("professor", "Professeur Mystère").strip()
            credits   = int(request.form.get("credits", 5) or 5)
            color     = request.form.get("color", "")

            if not name:
                flash("Le nom du cours est obligatoire !", "error")
                return render_template("course_form.html")

            new_course = Course(name=name, professor=professor, credits=credits, color=color)
            course_mgr.add(new_course)
            flash(f"✅ Cours '{name}' ajouté !", "success")
            return redirect(url_for("courses_list"))

        except ValueError as e:
            flash(f"Erreur : {str(e)}", "error")

    return render_template("course_form.html")


@app.route("/courses/<course_id>/delete", methods=["POST"])
def course_delete(course_id: str):
    """Supprime un cours (et désassocie les deadlines liées)."""
    course = course_mgr.get_by_id(course_id)
    if course:
        # Désassociation des deadlines liées
        for dl in deadline_mgr.get_by_course(course_id):
            dl.course_id = ""
            deadline_mgr.update(dl)
        course_mgr.delete(course_id)
        flash(f"🗑️ Cours '{course.name}' supprimé.", "info")
    else:
        flash("Cours introuvable.", "error")
    return redirect(url_for("courses_list"))


# =============================================================
#  ROUTE : Rapport IA
# =============================================================

@app.route("/ai-report")
def ai_report():
    """
    Génère et affiche le rapport d'analyse IA complet.

    Instancie AIAdvisor avec les deadlines actives et les cours,
    puis lance l'analyse complète.
    """
    active_deadlines = deadline_mgr.get_active()
    courses_dict     = course_mgr.get_as_dict()

    # Instanciation et lancement de l'analyse IA
    advisor  = AIAdvisor(deadlines=active_deadlines, courses=courses_dict)
    analysis = advisor.analyze()

    return render_template(
        "ai_report.html",
        analysis = analysis.to_dict(),
        today    = date.today(),
    )


# =============================================================
#  ROUTE : API JSON (pour les graphiques JS)
# =============================================================

@app.route("/api/stats")
def api_stats():
    """
    Endpoint API JSON — retourne les statistiques pour les graphiques Chart.js.
    Consommé par le JavaScript côté client (fetch API).
    """
    all_deadlines = deadline_mgr.get_all()
    courses_dict  = course_mgr.get_as_dict()

    # Distribution des priorités
    priority_dist = {p.name: 0 for p in Priority}
    for dl in deadline_mgr.get_active():
        priority_dist[dl.priority.name] += 1

    # Distribution des statuts
    status_dist = {s.value: 0 for s in Status}
    for dl in all_deadlines:
        status_dist[dl.status.value] += 1

    # Stress scores pour les 10 prochaines deadlines
    stress_data = []
    for dl in deadline_mgr.get_sorted_by_stress()[:10]:
        course = courses_dict.get(dl.course_id)
        stress_data.append({
            "title":       dl.title[:25],
            "stress":      dl.stress_score,
            "days":        dl.days_remaining,
            "course_name": course.name[:20] if course else "—",
            "color":       course.color if course else "#CCCCCC",
        })

    return jsonify({
        "stats":         deadline_mgr.get_stats(),
        "priority_dist": priority_dist,
        "status_dist":   status_dist,
        "stress_data":   stress_data,
    })


# =============================================================
#  Lancement de l'Application
# =============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  🎓 DeadlineMap ICHEC - Tableau de Bord Anti-Stress")
    print("  🏫 Campus Montgomery & Anjou")
    print("=" * 60)
    print(f"  📁 Données : {DATA_FILE}")
    print(f"  🌐 URL     : http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, host="127.0.0.1", port=5000)
