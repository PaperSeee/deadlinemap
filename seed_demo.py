"""
============================================================
  DeadlineMap - seed_demo.py
  Script de peuplement avec des données de démonstration
  Exécuter une seule fois : python3 seed_demo.py
============================================================
"""
from datetime import date, timedelta
from models import Deadline, Course, Priority, Status
from manager import DeadlineManager, CourseManager

DATA_FILE = "data/deadlinemap.json"
dl_mgr  = DeadlineManager(DATA_FILE)
c_mgr   = CourseManager(DATA_FILE)

# Seed les cours ICHEC si pas déjà fait
if not c_mgr.get_all():
    c_mgr.seed_ichec_courses()

courses = {c.name: c for c in c_mgr.get_all()}

today = date.today()

# Données de démo réalistes
demo_deadlines = [
    Deadline(
        title="Rapport final Analyse Financière — Chapitres 4-7",
        due_date=today + timedelta(days=2),
        course_id=courses.get("Gestion Financière", c_mgr.get_all()[0]).id,
        priority=Priority.CRITIQUE,
        status=Status.EN_COURS,
        estimated_hours=12.0,
        description="Format APA, 20 pages min. Voir consignes Moodle semaine 10.",
    ),
    Deadline(
        title="Examen blanc Droit des Sociétés",
        due_date=today + timedelta(days=5),
        course_id=courses.get("Droit des Sociétés", c_mgr.get_all()[1]).id,
        priority=Priority.ELEVE,
        status=Status.A_FAIRE,
        estimated_hours=6.0,
        description="Réviser chapitres 3 à 8 du syllabus.",
    ),
    Deadline(
        title="Présentation Marketing Digital — Pitch startup",
        due_date=today + timedelta(days=9),
        course_id=courses.get("Marketing Digital", c_mgr.get_all()[2]).id,
        priority=Priority.ELEVE,
        status=Status.EN_COURS,
        estimated_hours=8.0,
        description="Slides PowerPoint (15 max), demo 10 minutes.",
    ),
    Deadline(
        title="TFE — Soumission plan détaillé",
        due_date=today + timedelta(days=14),
        course_id=courses.get("TFE (Travail de Fin d'Études)", c_mgr.get_all()[0]).id,
        priority=Priority.CRITIQUE,
        status=Status.A_FAIRE,
        estimated_hours=20.0,
        description="10 pages, bibliographie, méthodologie. Deadline DURE.",
    ),
    Deadline(
        title="Cas pratique Comptabilité Approfondie",
        due_date=today + timedelta(days=4),
        course_id=courses.get("Comptabilité Approfondie", c_mgr.get_all()[0]).id,
        priority=Priority.MOYEN,
        status=Status.A_FAIRE,
        estimated_hours=4.5,
        description="Exercice 12 du livret + bilan consolidé.",
    ),
    Deadline(
        title="Étude de cas Management Stratégique",
        due_date=today + timedelta(days=18),
        course_id=courses.get("Management Stratégique", c_mgr.get_all()[0]).id,
        priority=Priority.MOYEN,
        status=Status.A_FAIRE,
        estimated_hours=7.0,
        description="Analyse SWOT d'une entreprise belge au choix.",
    ),
    Deadline(
        title="Synthèse Économie Internationale",
        due_date=today + timedelta(days=25),
        course_id=courses.get("Économie Internationale", c_mgr.get_all()[0]).id,
        priority=Priority.FAIBLE,
        status=Status.A_FAIRE,
        estimated_hours=3.0,
        description="Résumé 5 pages sur l'impact Brexit sur le Benelux.",
    ),
    Deadline(
        title="TP Statistiques — Analyse régression",
        due_date=today + timedelta(days=12),
        course_id=courses.get("Statistiques Appliquées", c_mgr.get_all()[0]).id,
        priority=Priority.MOYEN,
        status=Status.A_FAIRE,
        estimated_hours=5.0,
        description="Dataset fourni sur Moodle. Utiliser Excel ou R.",
    ),
]

# Ajouter seulement si aucune deadline n'existe
if not dl_mgr.get_all():
    for dl in demo_deadlines:
        dl_mgr.add(dl)
    print(f"✅ {len(demo_deadlines)} deadlines de démo ajoutées !")
else:
    print(f"ℹ️  {len(dl_mgr.get_all())} deadline(s) déjà présente(s). Seed ignoré.")

print("🚀 Lance l'app avec : python3 app.py")
