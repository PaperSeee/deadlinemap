"""
============================================================
  DeadlineMap - manager.py
  Couche de Persistance et de Gestion (Pattern Repository)
============================================================

ARCHITECTURE :

1. `DataManager` (classe de base abstraite) :
   - Gère la lecture/écriture JSON (persistance sans base de données).
   - Principe SRP (Single Responsibility Principle) : une classe = un rôle.

2. `DeadlineManager(DataManager)` → HÉRITAGE :
   - Hérite de DataManager pour la persistance.
   - Ajoute les opérations CRUD sur les Deadlines.
   - Ajoute les méthodes de tri et de filtrage.

3. `CourseManager(DataManager)` → HÉRITAGE :
   - Idem pour les Cours.

PATTERN APPLIQUÉ : Repository Pattern
   Permet de découpler la logique métier de la source de données.
   Si on voulait passer à une vraie DB (SQLite, PostgreSQL),
   il suffirait de réécrire DataManager sans toucher au reste.
"""

import json
import os
from typing import List, Optional, Dict
from datetime import date, timedelta

from models import Deadline, Course, Priority, Status


# =============================================================
#  CLASSE DE BASE : DataManager (Persistance JSON)
# =============================================================

class DataManager:
    """
    Gère la persistance des données dans un fichier JSON.

    RÔLE : Abstraire l'accès aux données (lecture/écriture fichier).
    HÉRITAGE : DeadlineManager et CourseManager héritent de cette classe.

    Args:
        filepath : Chemin vers le fichier JSON de stockage.
    """

    def __init__(self, filepath: str):
        self._filepath = filepath
        # Crée le fichier avec une structure vide s'il n'existe pas
        if not os.path.exists(filepath):
            self._write_raw({})

    def _read_raw(self) -> dict:
        """Lit le contenu brut du fichier JSON."""
        try:
            with open(self._filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _write_raw(self, data: dict):
        """Écrit un dictionnaire dans le fichier JSON (avec indentation)."""
        with open(self._filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


# =============================================================
#  CLASSE FILLE : DeadlineManager (CRUD + Tri)
# =============================================================

class DeadlineManager(DataManager):
    """
    Gère toutes les opérations CRUD sur les Deadlines.

    HÉRITAGE : Hérite de DataManager pour la persistance JSON.
    RESPONSABILITÉ : Créer, lire, modifier, supprimer et trier les deadlines.

    La clé de stockage dans le JSON est "deadlines" (un dict {id: deadline_dict}).
    """

    STORAGE_KEY = "deadlines"

    def __init__(self, filepath: str):
        super().__init__(filepath)   # Appel constructeur parent
        # S'assure que la clé "deadlines" existe dans le JSON
        raw = self._read_raw()
        if self.STORAGE_KEY not in raw:
            raw[self.STORAGE_KEY] = {}
            self._write_raw(raw)

    # ---------- Méthodes privées de persistance ----------

    def _load_all_raw(self) -> dict:
        """Charge le dictionnaire brut {id: dict} depuis le JSON."""
        return self._read_raw().get(self.STORAGE_KEY, {})

    def _save_all_raw(self, deadlines_dict: dict):
        """Sauvegarde le dictionnaire complet dans le JSON."""
        raw = self._read_raw()
        raw[self.STORAGE_KEY] = deadlines_dict
        self._write_raw(raw)

    # ---------- CRUD Public ----------

    def get_all(self) -> List[Deadline]:
        """
        Retourne la liste de TOUTES les deadlines, triées par date.
        Auto-met-à-jour le statut EN_RETARD si nécessaire.

        Returns:
            Liste d'objets Deadline triés par date limite croissante.
        """
        raw = self._load_all_raw()
        deadlines = []
        modified = False

        for dl_dict in raw.values():
            try:
                dl = Deadline.from_dict(dl_dict)
                dl.auto_update_status()  # Met EN_RETARD si nécessaire

                # Si le statut a changé, on sauvegarde
                if dl.status.value != dl_dict.get("status"):
                    modified = True

                deadlines.append(dl)
            except (KeyError, ValueError) as e:
                # Ignore les entrées corrompues (robustesse)
                print(f"⚠️  Deadline corrompue ignorée: {e}")

        if modified:
            # Sauvegarde les statuts mis à jour
            self._save_all_raw({dl.id: dl.to_dict() for dl in deadlines})

        return sorted(deadlines, key=lambda d: d.due_date)

    def get_by_id(self, deadline_id: str) -> Optional[Deadline]:
        """
        Retourne une deadline par son ID.

        Args:
            deadline_id : UUID de la deadline.

        Returns:
            Objet Deadline ou None si non trouvé.
        """
        raw = self._load_all_raw()
        dl_dict = raw.get(deadline_id)
        if dl_dict:
            return Deadline.from_dict(dl_dict)
        return None

    def add(self, deadline: Deadline) -> Deadline:
        """
        Ajoute une nouvelle deadline dans le stockage.

        Args:
            deadline : Objet Deadline à persister.

        Returns:
            La même deadline (utile pour le chaînage).
        """
        raw = self._load_all_raw()
        raw[deadline.id] = deadline.to_dict()
        self._save_all_raw(raw)
        return deadline

    def update(self, deadline: Deadline) -> bool:
        """
        Met à jour une deadline existante.

        Args:
            deadline : Deadline avec les nouvelles valeurs.

        Returns:
            True si trouvée et mise à jour, False sinon.
        """
        raw = self._load_all_raw()
        if deadline.id not in raw:
            return False
        raw[deadline.id] = deadline.to_dict()
        self._save_all_raw(raw)
        return True

    def delete(self, deadline_id: str) -> bool:
        """
        Supprime une deadline par son ID.

        Args:
            deadline_id : UUID de la deadline à supprimer.

        Returns:
            True si supprimée, False si introuvable.
        """
        raw = self._load_all_raw()
        if deadline_id not in raw:
            return False
        del raw[deadline_id]
        self._save_all_raw(raw)
        return True

    # ---------- Méthodes de Filtrage et Tri ----------

    def get_by_course(self, course_id: str) -> List[Deadline]:
        """Retourne les deadlines filtrées par cours."""
        return [dl for dl in self.get_all() if dl.course_id == course_id]

    def get_active(self) -> List[Deadline]:
        """Retourne uniquement les deadlines non terminées."""
        return [dl for dl in self.get_all() if dl.status != Status.TERMINE]

    def get_overdue(self) -> List[Deadline]:
        """Retourne les deadlines en retard (date dépassée, non terminées)."""
        return [dl for dl in self.get_all() if dl.is_overdue()]

    def get_upcoming(self, days: int = 7) -> List[Deadline]:
        """
        Retourne les deadlines dans les X prochains jours.

        Args:
            days : Fenêtre de temps en jours (défaut: 7).
        """
        limit = date.today() + timedelta(days=days)
        return [
            dl for dl in self.get_active()
            if date.today() <= dl.due_date <= limit
        ]

    def get_sorted_by_stress(self) -> List[Deadline]:
        """Retourne les deadlines triées par score de stress décroissant."""
        return sorted(self.get_active(), key=lambda d: d.stress_score, reverse=True)

    def get_stats(self) -> dict:
        """
        Calcule les statistiques globales pour le tableau de bord.

        Returns:
            Dictionnaire avec les métriques clés.
        """
        all_dl   = self.get_all()
        active   = self.get_active()
        overdue  = self.get_overdue()
        upcoming = self.get_upcoming(7)

        avg_stress = (
            sum(dl.stress_score for dl in active) / len(active)
            if active else 0
        )

        return {
            "total":          len(all_dl),
            "total_active":   len(active),
            "active":         len(active),
            "overdue_count":  len(overdue),
            "overdue":        len(overdue),
            "upcoming_7days": len(upcoming),
            "upcoming_7d":    len(upcoming),
            "completed_count":len([dl for dl in all_dl if dl.status == Status.TERMINE]),
            "completed":      len([dl for dl in all_dl if dl.status == Status.TERMINE]),
            "avg_stress":     round(avg_stress, 1),
            "max_stress":     max((dl.stress_score for dl in active), default=0),
        }


# =============================================================
#  CLASSE FILLE : CourseManager (CRUD Cours)
# =============================================================

class CourseManager(DataManager):
    """
    Gère toutes les opérations CRUD sur les Cours.

    HÉRITAGE : Hérite de DataManager.
    RESPONSABILITÉ : Créer, lire, modifier, supprimer les cours.
    """

    STORAGE_KEY = "courses"

    def __init__(self, filepath: str):
        super().__init__(filepath)
        raw = self._read_raw()
        if self.STORAGE_KEY not in raw:
            raw[self.STORAGE_KEY] = {}
            self._write_raw(raw)

    def _load_all_raw(self) -> dict:
        return self._read_raw().get(self.STORAGE_KEY, {})

    def _save_all_raw(self, courses_dict: dict):
        raw = self._read_raw()
        raw[self.STORAGE_KEY] = courses_dict
        self._write_raw(raw)

    def get_all(self) -> List[Course]:
        """Retourne tous les cours triés par nom."""
        raw = self._load_all_raw()
        courses = []
        for c_dict in raw.values():
            try:
                courses.append(Course.from_dict(c_dict))
            except (KeyError, ValueError) as e:
                print(f"⚠️  Cours corrompu ignoré: {e}")
        return sorted(courses, key=lambda c: c.name)

    def get_by_id(self, course_id: str) -> Optional[Course]:
        raw = self._load_all_raw()
        c_dict = raw.get(course_id)
        return Course.from_dict(c_dict) if c_dict else None

    def get_as_dict(self) -> Dict[str, Course]:
        """Retourne un dict {id: Course} pour les lookups rapides."""
        return {c.id: c for c in self.get_all()}

    def add(self, course: Course) -> Course:
        raw = self._load_all_raw()
        raw[course.id] = course.to_dict()
        self._save_all_raw(raw)
        return course

    def update(self, course: Course) -> bool:
        raw = self._load_all_raw()
        if course.id not in raw:
            return False
        raw[course.id] = course.to_dict()
        self._save_all_raw(raw)
        return True

    def delete(self, course_id: str) -> bool:
        raw = self._load_all_raw()
        if course_id not in raw:
            return False
        del raw[course_id]
        self._save_all_raw(raw)
        return True

    def seed_ichec_courses(self):
        """
        Pré-rempli avec les cours typiques de l'ICHEC Bachelor 2.
        Appelé au premier lancement pour avoir des données de démonstration.
        """
        ichec_courses = [
            Course("Gestion Financière",       "M. Vandenberghe",  6, "#FF6B6B"),
            Course("Droit des Sociétés",        "Mme Lecomte",      4, "#4ECDC4"),
            Course("Marketing Digital",         "M. Pirard",        5, "#45B7D1"),
            Course("Économie Internationale",   "Mme Fontaine",     5, "#96CEB4"),
            Course("Comptabilité Approfondie",  "M. Bastin",        6, "#FFEAA7"),
            Course("Management Stratégique",    "Mme Delcourt",     4, "#DDA0DD"),
            Course("TFE (Travail de Fin d'Études)", "Directeur TFE", 15, "#FF4757"),
            Course("Statistiques Appliquées",   "M. Claes",         4, "#2ED573"),
        ]
        for course in ichec_courses:
            self.add(course)
