"""
============================================================
  DeadlineMap - models.py
  Couche de Modèles (POO - Cœur de l'Architecture)
============================================================

ARCHITECTURE POO - EXPLICATION DES CHOIX :

1. Classe de Base `Task` :
   - Représente toute "tâche" générique dans le système.
   - Contient les attributs communs (id, titre, description, dates).
   - Principe : Abstraction et réutilisabilité.

2. Classe `Deadline(Task)` → HÉRITAGE :
   - Hérite de Task car une deadline EST une tâche (relation "is-a").
   - Ajoute les attributs spécifiques : date limite, cours, priorité, etc.
   - Override de `__repr__` pour affichage personnalisé.

3. Classe `Course` :
   - Entité indépendante représentant un cours ICHEC.
   - Associée à une Deadline via `course_id` (relation "has-a").

4. Classe `Priority` (Enum) :
   - Encapsule les niveaux de priorité avec des valeurs numériques.
   - Évite les "magic strings" et garantit la cohérence.

5. Classe `Status` (Enum) :
   - Cycle de vie d'une deadline (À faire → En cours → Terminé).

PRINCIPES POO APPLIQUÉS :
   - Encapsulation : attributs privés (_id) avec propriétés (@property)
   - Héritage : Deadline hérite de Task
   - Polymorphisme : méthode to_dict() redéfinie dans chaque classe
   - Abstraction : méthodes utilitaires cachant la complexité (stress_score)
"""

import uuid
import json
from abc import ABC, abstractmethod
from datetime import datetime, date
from enum import Enum
from typing import Optional


# =============================================================
#  ENUMS : Priorité et Statut (Encapsulation des constantes)
# =============================================================

class Priority(Enum):
    """
    Énumération des niveaux de priorité.
    La valeur numérique sert au tri et au calcul du stress.
    """
    FAIBLE    = 1   # "Bof, j'ai le temps..."
    MOYEN     = 2   # "Faudrait quand même s'y mettre"
    ELEVE     = 3   # "Sérieusement, commence maintenant"
    CRITIQUE  = 4   # "PANIQUE TOTALE - TFE demain 8h"

    @classmethod
    def from_string(cls, value: str) -> "Priority":
        """Convertit une chaîne (ex: 'ELEVE') en enum Priority."""
        mapping = {
            "FAIBLE": cls.FAIBLE,
            "MOYEN": cls.MOYEN,
            "ELEVE": cls.ELEVE,
            "CRITIQUE": cls.CRITIQUE,
        }
        return mapping.get(value.upper(), cls.MOYEN)

    def label_fr(self) -> str:
        """Retourne un label en français pour l'affichage UI."""
        labels = {
            "FAIBLE":   "🟢 Faible",
            "MOYEN":    "🟡 Moyen",
            "ELEVE":    "🟠 Élevé",
            "CRITIQUE": "🔴 CRITIQUE",
        }
        return labels.get(self.name, self.name)

    def css_class(self) -> str:
        """Retourne la classe CSS correspondante pour le style cartoon."""
        classes = {
            "FAIBLE":   "priority-low",
            "MOYEN":    "priority-medium",
            "ELEVE":    "priority-high",
            "CRITIQUE": "priority-critical",
        }
        return classes.get(self.name, "priority-medium")


class Status(Enum):
    """
    Cycle de vie d'une deadline.
    Permet de suivre l'avancement sans ambiguïté.
    """
    A_FAIRE     = "A_FAIRE"     # Pas encore commencé (comme ton TFE depuis 2 mois)
    EN_COURS    = "EN_COURS"    # En plein dedans (café en main)
    TERMINE     = "TERMINE"     # GG ! Tu peux guindailler ce soir
    EN_RETARD   = "EN_RETARD"   # Appelle ta prof, invente une excuse

    def label_fr(self) -> str:
        labels = {
            "A_FAIRE":   "📋 À faire",
            "EN_COURS":  "⚡ En cours",
            "TERMINE":   "✅ Terminé",
            "EN_RETARD": "🔥 EN RETARD",
        }
        return labels.get(self.value, self.value)

    def css_class(self) -> str:
        classes = {
            "A_FAIRE":   "status-todo",
            "EN_COURS":  "status-inprogress",
            "TERMINE":   "status-done",
            "EN_RETARD": "status-late",
        }
        return classes.get(self.value, "status-todo")


# =============================================================
#  CLASSE DE BASE : Task (Abstraction générique)
# =============================================================

class Task(ABC):
    """
    Classe de BASE ABSTRAITE (Abstract Base Class — ABC) représentant une tâche générique.

    RÔLE : Factoriser les attributs et méthodes communs à toutes
    les tâches (id unique, titre, description, timestamp de création).
    Toute entité 'à faire' dans le système hérite de cette classe.

    POURQUOI ABSTRAITE ?
    ─────────────────────
    On ne peut PAS instancier Task directement (Task() → TypeError).
    Cela force les sous-classes (Deadline) à implémenter to_dict().
    C'est le principe du Contrat Abstrait (Design by Contract).
    Référence : Patron de conception Template Method (GoF).

    Attributs privés (encapsulation) :
        _id          : Identifiant unique (UUID)
        _title       : Titre de la tâche
        _description : Description détaillée
        _created_at  : Date de création (auto)
        _updated_at  : Date de dernière modification
    """

    def __init__(self, title: str, description: str = "", task_id: Optional[str] = None):
        """
        Constructeur de Task.

        Args:
            title       : Titre obligatoire de la tâche.
            description : Description optionnelle.
            task_id     : UUID fourni (ex: chargement depuis JSON) ou auto-généré.
        """
        # Encapsulation : attributs privés, accessibles via @property
        self._id          = task_id if task_id else str(uuid.uuid4())
        self._title       = title
        self._description = description
        self._created_at  = datetime.now()
        self._updated_at  = datetime.now()

    # --- Propriétés (getters/setters encapsulés) ---

    @property
    def id(self) -> str:
        """Retourne l'ID unique de la tâche (lecture seule)."""
        return self._id

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str):
        """Valide que le titre n'est pas vide avant de le modifier."""
        if not value or not value.strip():
            raise ValueError("Le titre d'une tâche ne peut pas être vide !")
        self._title = value.strip()
        self._updated_at = datetime.now()

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, value: str):
        self._description = value
        self._updated_at = datetime.now()

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    def __eq__(self, other: object) -> bool:
        """
        Opérateur d'égalité structurelle entre deux tâches.
        Deux tâches sont identiques si et seulement si leurs IDs sont égaux.
        Permet d'utiliser 'deadline_a == deadline_b' proprement.
        """
        if not isinstance(other, Task):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        """
        Hash basé sur l'ID unique (immuable).
        Nécessaire pour utiliser les objets Task dans des sets ou
        comme clés de dictionnaire (ex: {deadline: score}).
        """
        return hash(self._id)

    @abstractmethod
    def to_dict(self) -> dict:
        """
        Méthode ABSTRAITE : chaque sous-classe DOIT implémenter sa propre
        sérialisation en dictionnaire (contrat imposé par ABC).
        Principe du Polymorphisme + Design by Contract.

        Sans @abstractmethod, une sous-classe oubliant to_dict() serait
        silencieusement incorrecte. Avec ABC → TypeError à l'instanciation.
        """
        return {
            "id":          self._id,
            "title":       self._title,
            "description": self._description,
            "created_at":  self._created_at.isoformat(),
            "updated_at":  self._updated_at.isoformat(),
            "type":        self.__class__.__name__,   # Pour savoir quelle classe reconstruire
        }

    def __repr__(self) -> str:
        """Représentation développeur de l'objet."""
        return f"<{self.__class__.__name__} id={self._id[:8]}... title='{self._title}'>"

    def __str__(self) -> str:
        """Représentation lisible par l'humain."""
        return self._title


# =============================================================
#  CLASSE FILLE : Deadline (Héritage de Task)
# =============================================================

class Deadline(Task):
    """
    Représente une deadline académique spécifique à l'ICHEC.

    HÉRITAGE : Hérite de Task (relation "is-a" → une deadline EST une tâche).
    EXTENSION : Ajoute les attributs propres au contexte académique :
                date limite, cours, priorité, statut, heures estimées.

    Méthodes calculées importantes :
        days_remaining  → Nombre de jours restants (négatif = retard)
        stress_score    → Score de stress de 0 à 100 (pour les jauges UI)
        urgency_label   → Message humoristique contextuel

    Args:
        title           : Ex: "Analyse financière - Rapport final"
        due_date        : Date limite (objet date Python)
        course_id       : ID du cours associé
        priority        : Niveau de priorité (enum Priority)
        status          : Statut actuel (enum Status)
        estimated_hours : Heures de travail estimées (ex: 8.5)
        description     : Notes supplémentaires
        task_id         : UUID (fourni pour le chargement depuis JSON)
    """

    def __init__(
        self,
        title:           str,
        due_date:        date,
        course_id:       str        = "",
        priority:        Priority   = Priority.MOYEN,
        status:          Status     = Status.A_FAIRE,
        estimated_hours: float      = 0.0,
        description:     str        = "",
        task_id:         Optional[str] = None,
    ):
        # Appel du constructeur parent (super()) → Bonne pratique POO
        super().__init__(title=title, description=description, task_id=task_id)

        # Attributs spécifiques à Deadline
        self._due_date        = due_date
        self._course_id       = course_id
        self._priority        = priority
        self._status          = status
        self._estimated_hours = estimated_hours

    # --- Propriétés spécifiques à Deadline ---

    @property
    def due_date(self) -> date:
        return self._due_date

    @due_date.setter
    def due_date(self, value: date):
        self._due_date  = value
        self._updated_at = datetime.now()

    @property
    def course_id(self) -> str:
        return self._course_id

    @course_id.setter
    def course_id(self, value: str):
        self._course_id  = value
        self._updated_at = datetime.now()

    @property
    def priority(self) -> Priority:
        return self._priority

    @priority.setter
    def priority(self, value: Priority):
        self._priority   = value
        self._updated_at = datetime.now()

    @property
    def status(self) -> Status:
        return self._status

    @status.setter
    def status(self, value: Status):
        self._status     = value
        self._updated_at = datetime.now()

    @property
    def estimated_hours(self) -> float:
        return self._estimated_hours

    @estimated_hours.setter
    def estimated_hours(self, value: float):
        if value < 0:
            raise ValueError("Les heures estimées ne peuvent pas être négatives !")
        self._estimated_hours = value
        self._updated_at      = datetime.now()

    # --- Méthodes calculées (logique métier) ---

    @property
    def days_remaining(self) -> int:
        """
        Calcule le nombre de jours restants avant la deadline.
        Retourne une valeur négative si la deadline est dépassée.
        """
        delta = self._due_date - date.today()
        return delta.days

    @property
    def stress_score(self) -> int:
        """
        Calcule un score de stress de 0 à 100 basé sur :
        - Le nombre de jours restants
        - La priorité de la tâche
        - Le statut (terminé = 0)

        Algorithme :
            score_temps    : Plus les jours restants sont faibles → score élevé
            score_priorité : Multiplie par le niveau de priorité
            Normalisation  : Ramène entre 0 et 100

        Retourne:
            int: Score entre 0 (zéro stress) et 100 (appel à maman)
        """
        # Une deadline terminée ne stresse plus !
        if self._status == Status.TERMINE:
            return 0

        days = self.days_remaining

        # En retard → stress maximum immédiat
        if days < 0:
            return 100

        # Score temporel : décroit linéairement de 100 (aujourd'hui) à 0 (30j+)
        if days == 0:
            score_temps = 100
        elif days <= 1:
            score_temps = 95
        elif days <= 3:
            score_temps = 85
        elif days <= 7:
            score_temps = 65
        elif days <= 14:
            score_temps = 40
        elif days <= 21:
            score_temps = 20
        else:
            score_temps = max(0, 100 - days * 2)

        # Pondération par la priorité
        priority_weights = {
            Priority.FAIBLE:   0.5,
            Priority.MOYEN:    0.75,
            Priority.ELEVE:    1.0,
            Priority.CRITIQUE: 1.25,
        }
        weight = priority_weights.get(self._priority, 1.0)

        # Score final normalisé entre 0 et 100
        return min(100, int(score_temps * weight))

    @property
    def urgency_label(self) -> str:
        """
        Génère un message humoristique et contextuel basé sur le score de stress.
        C'est ici que la touche ICHEC prend tout son sens !
        """
        if self._status == Status.TERMINE:
            return "✅ GG ! Tu peux aller te chercher un Vedett à Anjou !"

        days = self.days_remaining
        score = self.stress_score

        if days < 0:
            return "🔥 TROP TARD ! Appelle le secrétariat de Montgomery... Bonne chance !"
        elif days == 0:
            return "💀 C'EST AUJOURD'HUI !! Lâche TikTok MAINTENANT !!"
        elif days == 1:
            return "🚨 DEMAIN !! Le mode blocus est activé d'office, désolé."
        elif score >= 85:
            return "😱 PANIQUE TOTALE ! Même ta guindaille du jeudi est annulée."
        elif score >= 65:
            return "⚡ Alerte rouge ! Commence avant que ton prof t'envoie un mail."
        elif score >= 40:
            return "⚠️ Attention ! Ne reporte pas à demain ce que tu peux faire ce soir."
        elif score >= 20:
            return "📌 À surveiller. Profite, mais ne traîne pas trop."
        else:
            return "😎 Cool pour l'instant. Mais reviens dans quelques jours !"

    def is_overdue(self) -> bool:
        """Retourne True si la deadline est dépassée et pas encore terminée."""
        return self.days_remaining < 0 and self._status != Status.TERMINE

    def auto_update_status(self):
        """
        Met à jour automatiquement le statut EN_RETARD si la date est dépassée.
        Appelée automatiquement lors des chargements et sauvegardes.
        """
        if self.is_overdue() and self._status not in (Status.TERMINE, Status.EN_RETARD):
            self._status = Status.EN_RETARD

    def to_dict(self) -> dict:
        """
        Surcharge (polymorphisme) de to_dict() de la classe mère Task.
        Ajoute les attributs spécifiques à Deadline pour la persistance JSON.
        """
        # On commence par le dict de la classe mère (super())
        base = super().to_dict()
        # On ajoute/surcharge avec les attributs de Deadline
        base.update({
            "due_date":        self._due_date.isoformat(),
            "course_id":       self._course_id,
            "priority":        self._priority.name,
            "status":          self._status.value,
            "estimated_hours": self._estimated_hours,
            # Champs calculés (non persistés mais utiles pour le JS / templates)
            "days_remaining":  self.days_remaining,
            "stress_score":    self.stress_score,
            "urgency_label":   self.urgency_label,
            "priority_label":  self._priority.label_fr(),
            "status_label":    self._status.label_fr(),
            "priority_css":    self._priority.css_class(),
            "status_css":      self._status.css_class(),
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "Deadline":
        """
        Méthode de fabrique (Factory Method - Design Pattern) :
        Reconstruit un objet Deadline depuis un dictionnaire JSON.

        Args:
            data: Dictionnaire chargé depuis le fichier JSON.

        Returns:
            Instance de Deadline correctement reconstruite.
        """
        return cls(
            title           = data["title"],
            due_date        = date.fromisoformat(data["due_date"]),
            course_id       = data.get("course_id", ""),
            priority        = Priority.from_string(data.get("priority", "MOYEN")),
            status          = Status(data.get("status", "A_FAIRE")),
            estimated_hours = float(data.get("estimated_hours", 0.0)),
            description     = data.get("description", ""),
            task_id         = data.get("id"),
        )

    def __repr__(self) -> str:
        """Override du __repr__ parent pour inclure la date limite."""
        return (
            f"<Deadline id={self._id[:8]}... "
            f"title='{self._title}' "
            f"due={self._due_date} "
            f"days_left={self.days_remaining} "
            f"stress={self.stress_score}%>"
        )


# =============================================================
#  CLASSE : Course (Entité indépendante)
# =============================================================

class Course:
    """
    Représente un cours de l'ICHEC.

    RELATION avec Deadline : Une Deadline "appartient à" un Course (has-a).
    La liaison est faite via course_id dans Deadline.

    Attributs :
        _id        : UUID unique du cours
        _name      : Nom du cours (ex: "Gestion Financière B2")
        _professor : Nom du prof (ex: "M. Dupont")
        _credits   : Nombre de crédits ECTS
        _color     : Couleur HEX pour le design cartoon (ex: "#FF6B6B")
    """

    # Palette de couleurs cartoon prédéfinies pour les cours ICHEC
    COLOR_PALETTE = [
        "#FF6B6B",  # Rouge vif
        "#4ECDC4",  # Turquoise
        "#45B7D1",  # Bleu clair
        "#96CEB4",  # Vert menthe
        "#FFEAA7",  # Jaune pop
        "#DDA0DD",  # Violet prune
        "#98D8C8",  # Vert eau
        "#F7DC6F",  # Jaune doré
        "#BB8FCE",  # Lilas
        "#82E0AA",  # Vert tendre
    ]

    _color_index = 0  # Variable de classe pour alterner les couleurs automatiquement

    def __init__(
        self,
        name:      str,
        professor: str   = "Professeur Mystère",
        credits:   int   = 5,
        color:     str   = "",
        course_id: Optional[str] = None,
    ):
        self._id        = course_id if course_id else str(uuid.uuid4())
        self._name      = name
        self._professor = professor
        self._credits   = credits

        # Attribution automatique d'une couleur si non fournie
        if color:
            self._color = color
        else:
            self._color = Course.COLOR_PALETTE[Course._color_index % len(Course.COLOR_PALETTE)]
            Course._color_index += 1

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        if not value.strip():
            raise ValueError("Le nom du cours ne peut pas être vide !")
        self._name = value.strip()

    @property
    def professor(self) -> str:
        return self._professor

    @professor.setter
    def professor(self, value: str):
        self._professor = value.strip()

    @property
    def credits(self) -> int:
        return self._credits

    @property
    def color(self) -> str:
        return self._color

    @color.setter
    def color(self, value: str):
        self._color = value

    def to_dict(self) -> dict:
        """Sérialise le cours en dictionnaire JSON."""
        return {
            "id":        self._id,
            "name":      self._name,
            "professor": self._professor,
            "credits":   self._credits,
            "color":     self._color,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Course":
        """Factory Method : reconstruit un Course depuis un dictionnaire."""
        return cls(
            name      = data["name"],
            professor = data.get("professor", "Professeur Mystère"),
            credits   = int(data.get("credits", 5)),
            color     = data.get("color", ""),
            course_id = data.get("id"),
        )

    def __repr__(self) -> str:
        return f"<Course id={self._id[:8]}... name='{self._name}' prof='{self._professor}'>"

    def __str__(self) -> str:
        return f"{self._name} ({self._professor})"
