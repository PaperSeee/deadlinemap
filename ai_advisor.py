"""
============================================================
  DeadlineMap - ai_advisor.py
  Module IA / Analyse Prédictive de Charge de Travail
============================================================

ARCHITECTURE :

1. `Alert` : Dataclass représentant une alerte générée par le système.

2. `WorkloadAnalysis` : Dataclass contenant les résultats d'une analyse.

3. `AIAdvisor` : Classe principale du module IA.
   - Analyse la charge de travail globale.
   - Détecte les "semaines de rush" (plusieurs deadlines critiques simultanées).
   - Génère des recommandations personnalisées avec humour ICHEC.
   - Simule un moteur IA via des règles algorithmiques avancées.

SIMULATION IA :
   Vu l'absence d'une clé API dans ce projet, l'IA est simulée via
   un moteur de règles (rule-based system) avancé. C'est une approche
   valide et expliquable académiquement : deterministic expert system.
   Si une clé OpenAI/Mistral était disponible, on remplacerait
   la méthode `_generate_advice` par un appel API réel.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from datetime import date, timedelta
from collections import defaultdict

from models import Deadline, Course, Priority, Status


# =============================================================
#  DATACLASS : Alert
# =============================================================

@dataclass
class Alert:
    """
    Représente une alerte générée par le système IA.

    DATACLASS : Python 3.7+ - génère automatiquement __init__, __repr__, etc.
    C'est une alternative légère aux classes classiques pour les
    objets principalement porteurs de données.

    Attributs :
        level    : Niveau de sévérité ("info", "warning", "danger", "critical")
        title    : Titre court de l'alerte
        message  : Message détaillé avec contexte ICHEC
        icon     : Emoji représentatif
        deadline_ids : IDs des deadlines concernées (peut être vide)
    """
    level:        str
    title:        str
    message:      str
    icon:         str = "📌"
    deadline_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "level":        self.level,
            "title":        self.title,
            "message":      self.message,
            "icon":         self.icon,
            "deadline_ids": self.deadline_ids,
        }


# =============================================================
#  DATACLASS : WorkloadAnalysis
# =============================================================

@dataclass
class WorkloadAnalysis:
    """
    Résultat complet d'une analyse de charge de travail.

    Produit par AIAdvisor.analyze() et consommé par les templates Flask.
    """
    global_stress_score:  int           # Score global 0-100
    stress_label:         str           # Label humain du stress global
    weekly_load:          Dict[str, int] # {semaine_str: nb_deadlines}
    rush_weeks:           List[str]      # Semaines avec ≥3 deadlines actives
    total_estimated_hours: float         # Total heures de travail estimé
    alerts:               List[Alert]   # Liste des alertes générées
    recommendations:      List[str]     # Conseils personnalisés
    most_urgent:          List[dict]    # Top 3 deadlines les plus urgentes
    advice_summary:       str           # Résumé global style "IA"

    def to_dict(self) -> dict:
        return {
            "global_stress_score":   self.global_stress_score,
            "stress_label":          self.stress_label,
            "weekly_load":           self.weekly_load,
            "rush_weeks":            self.rush_weeks,
            "total_estimated_hours": self.total_estimated_hours,
            "alerts":                [a.to_dict() for a in self.alerts],
            "recommendations":       self.recommendations,
            "most_urgent":           self.most_urgent,
            "advice_summary":        self.advice_summary,
        }


# =============================================================
#  CLASSE PRINCIPALE : AIAdvisor
# =============================================================

class AIAdvisor:
    """
    Moteur d'analyse IA de la charge de travail étudiante.

    SIMULATION IA (Expert System / Rule-Based AI) :
    ─────────────────────────────────────────────────
    Cette classe implémente un système expert déterministe qui :
    1. Analyse les patterns de distribution des deadlines dans le temps.
    2. Détecte les clusters de surcharge (plusieurs deadlines proches).
    3. Estime la charge horaire totale et hebdomadaire.
    4. Applique des règles de priorité pour générer des recommandations.
    5. Produit des messages personnalisés au contexte ICHEC.

    C'est une approche de "Symbolic AI" (IA symbolique) par opposition
    aux modèles de ML/DL. Elle est:
    - Explicable (on peut justifier chaque décision)
    - Reproductible (résultats déterministes)
    - Adaptée à un contexte académique où l'interprétabilité compte

    Args:
        deadlines : Liste des deadlines actives à analyser.
        courses   : Dictionnaire {id: Course} pour enrichir les données.
    """

    # Seuils de détection d'une "semaine de rush"
    RUSH_THRESHOLD             = 3    # ≥3 deadlines dans une semaine = RUSH
    CRITICAL_DAYS_WINDOW       = 3    # Fenêtre critique : 3 jours
    HIGH_WORKLOAD_HOURS        = 20   # >20h/semaine = surcharge
    STRESS_CRITICAL_THRESHOLD  = 75   # Score de stress global critique

    def __init__(self, deadlines: List[Deadline], courses: Dict[str, Course]):
        self._deadlines = [dl for dl in deadlines if dl.status != Status.TERMINE]
        self._courses   = courses

    def analyze(self) -> WorkloadAnalysis:
        """
        Point d'entrée principal : lance l'analyse complète.

        Étapes :
        1. Calcul du score de stress global
        2. Distribution hebdomadaire des deadlines
        3. Détection des semaines de rush
        4. Calcul des heures totales estimées
        5. Génération des alertes
        6. Génération des recommandations
        7. Assemblage du rapport final

        Returns:
            WorkloadAnalysis : Rapport complet prêt à afficher.
        """
        # Étape 1 : Score de stress global (moyenne pondérée)
        global_stress = self._compute_global_stress()
        stress_label  = self._stress_to_label(global_stress)

        # Étape 2 : Distribution hebdomadaire
        weekly_load = self._compute_weekly_distribution()

        # Étape 3 : Semaines de rush
        rush_weeks = self._detect_rush_weeks(weekly_load)

        # Étape 4 : Heures totales
        total_hours = sum(dl.estimated_hours for dl in self._deadlines)

        # Étape 5 : Génération des alertes
        alerts = self._generate_alerts(rush_weeks, global_stress)

        # Étape 6 : Recommandations
        recommendations = self._generate_recommendations(rush_weeks, global_stress, total_hours)

        # Étape 7 : Top 3 urgent
        most_urgent = self._get_most_urgent(3)

        # Étape 8 : Résumé global style "rapport IA"
        advice_summary = self._generate_advice_summary(global_stress, rush_weeks, total_hours)

        return WorkloadAnalysis(
            global_stress_score   = global_stress,
            stress_label          = stress_label,
            weekly_load           = weekly_load,
            rush_weeks            = rush_weeks,
            total_estimated_hours = total_hours,
            alerts                = alerts,
            recommendations       = recommendations,
            most_urgent           = most_urgent,
            advice_summary        = advice_summary,
        )

    # ─────────────────────────────────────────────────
    #  Méthodes Privées : Calculs
    # ─────────────────────────────────────────────────

    def _compute_global_stress(self) -> int:
        """
        Calcule le score de stress global en utilisant une moyenne pondérée.

        ALGORITHME :
        - Les deadlines à priorité CRITIQUE pèsent 2x plus.
        - Les deadlines à priorité ÉLEVÉ pèsent 1.5x plus.
        - Résultat normalisé entre 0 et 100.
        """
        if not self._deadlines:
            return 0

        total_weight = 0.0
        weighted_sum = 0.0

        priority_weights = {
            Priority.FAIBLE:   0.5,
            Priority.MOYEN:    1.0,
            Priority.ELEVE:    1.5,
            Priority.CRITIQUE: 2.0,
        }

        for dl in self._deadlines:
            weight = priority_weights.get(dl.priority, 1.0)
            weighted_sum += dl.stress_score * weight
            total_weight  += weight

        return min(100, int(weighted_sum / total_weight)) if total_weight > 0 else 0

    def _stress_to_label(self, score: int) -> str:
        """Convertit un score numérique en label textuel ICHEC-flavored."""
        if score >= 90:
            return "🔥 CATASTROPHIQUE - Mode survie activé"
        elif score >= 75:
            return "💀 CRITIQUE - Annule tes soirées"
        elif score >= 55:
            return "😰 ÉLEVÉ - Café et motivation obligatoires"
        elif score >= 35:
            return "⚡ MODÉRÉ - C'est gérable, mais bouge-toi"
        elif score >= 15:
            return "😊 FAIBLE - T'as le temps... pour l'instant"
        else:
            return "😎 TRANQUILLE - Profite, t'as rien de chaud"

    def _compute_weekly_distribution(self) -> Dict[str, int]:
        """
        Calcule le nombre de deadlines par semaine (ISO week).

        Returns:
            Dict {ISO_week_string: count}, ex: {"2026-W12": 3}
        """
        distribution: Dict[str, int] = defaultdict(int)

        for dl in self._deadlines:
            # Format ISO : "2026-W12" pour la semaine 12 de 2026
            iso_calendar = dl.due_date.isocalendar()
            week_key = f"{iso_calendar.year}-W{iso_calendar.week:02d}"
            distribution[week_key] += 1

        return dict(sorted(distribution.items()))

    def _detect_rush_weeks(self, weekly_load: Dict[str, int]) -> List[str]:
        """
        Identifie les semaines de "rush" (≥ RUSH_THRESHOLD deadlines).

        Returns:
            Liste des semaines ISO (ex: ["2026-W14", "2026-W18"])
        """
        return [
            week for week, count in weekly_load.items()
            if count >= self.RUSH_THRESHOLD
        ]

    def _get_most_urgent(self, n: int) -> List[dict]:
        """
        Retourne les N deadlines les plus urgentes (stress_score le plus élevé).
        Enrichit les données avec le nom du cours.
        """
        sorted_dl = sorted(self._deadlines, key=lambda d: d.stress_score, reverse=True)
        result = []

        for dl in sorted_dl[:n]:
            course = self._courses.get(dl.course_id)
            result.append({
                **dl.to_dict(),
                "course_name":  course.name  if course else "Cours inconnu",
                "course_color": course.color if course else "#CCCCCC",
            })

        return result

    # ─────────────────────────────────────────────────
    #  Méthodes Privées : Génération IA
    # ─────────────────────────────────────────────────

    def _generate_alerts(self, rush_weeks: List[str], global_stress: int) -> List[Alert]:
        """
        Génère une liste d'alertes basées sur les règles métier.

        RÈGLES APPLIQUÉES :
        R1 : Deadline dans les 24h → alerte CRITIQUE
        R2 : Semaine de rush détectée → alerte DANGER
        R3 : Deadline en retard → alerte CRITICAL
        R4 : Stress global > 75 → alerte WARNING
        R5 : Aucune deadline → message positif INFO
        """
        alerts: List[Alert] = []
        today = date.today()

        # R3 : Deadlines en retard
        overdue = [dl for dl in self._deadlines if dl.is_overdue()]
        if overdue:
            titles = ", ".join(dl.title[:30] for dl in overdue[:3])
            alerts.append(Alert(
                level        = "critical",
                title        = f"🔥 {len(overdue)} deadline(s) EN RETARD !",
                message      = (
                    f"Désolé de te l'annoncer, mais '{titles}' est dépassée. "
                    "Contacte ton prof MAINTENANT et négocie une extension. "
                    "L'honnêteté, ça marche parfois mieux qu'on croit à Montgomery."
                ),
                icon         = "🔥",
                deadline_ids = [dl.id for dl in overdue],
            ))

        # R1 : Deadline dans les 24h
        critical_24h = [dl for dl in self._deadlines if 0 <= dl.days_remaining <= 1]
        for dl in critical_24h:
            course = self._courses.get(dl.course_id)
            course_name = course.name if course else "ton cours"
            alerts.append(Alert(
                level        = "critical",
                title        = f"💀 '{dl.title}' - C'est DEMAIN (ou aujourd'hui !) !",
                message      = (
                    f"Pour {course_name} : il te reste "
                    f"{'moins de 24h' if dl.days_remaining == 0 else '1 jour'}. "
                    f"Estime: {dl.estimated_hours}h de travail. "
                    "TikTok est officiellement interdit jusqu'à la remise."
                ),
                icon         = "💀",
                deadline_ids = [dl.id],
            ))

        # R2 : Semaines de rush
        for week in rush_weeks:
            week_deadlines = [
                dl for dl in self._deadlines
                if f"{dl.due_date.isocalendar().year}-W{dl.due_date.isocalendar().week:02d}" == week
            ]
            count = len(week_deadlines)
            total_h = sum(dl.estimated_hours for dl in week_deadlines)
            alerts.append(Alert(
                level   = "danger",
                title   = f"⚡ Semaine de rush : {week} ({count} deadlines !)",
                message = (
                    f"L'IA détecte un cluster de {count} deadlines en {week}. "
                    f"Charge estimée : {total_h:.1f}h de boulot. "
                    "Commence la préparation AU MOINS 2 semaines à l'avance. "
                    "Conseil : annule la guindaille de cette semaine-là (pardon)."
                ),
                icon         = "⚡",
                deadline_ids = [dl.id for dl in week_deadlines],
            ))

        # R4 : Stress global élevé
        if global_stress >= self.STRESS_CRITICAL_THRESHOLD and not overdue:
            alerts.append(Alert(
                level   = "warning",
                title   = f"😰 Score de stress global: {global_stress}/100",
                message = (
                    "Ta charge de travail totale est élevée. "
                    "Prends 30 minutes maintenant pour décomposer tes tâches. "
                    "La Bibliothèque d'Anjou est ouverte jusqu'à 21h, pense-y !"
                ),
                icon = "😰",
            ))

        # R5 : Aucune deadline active → message positif
        if not self._deadlines:
            alerts.append(Alert(
                level   = "info",
                title   = "😎 Aucune deadline active !",
                message = (
                    "Félicitations ! Soit tu as tout rendu à temps "
                    "(champion !), soit tu as oublié d'encoder tes deadlines... "
                    "Dans le doute, vérifie ton Moodle ICHEC !"
                ),
                icon = "😎",
            ))

        return alerts

    def _generate_recommendations(
        self,
        rush_weeks:    List[str],
        global_stress: int,
        total_hours:   float,
    ) -> List[str]:
        """
        Génère une liste de recommandations personnalisées.
        Chaque règle déclenche un conseil spécifique.
        """
        recs: List[str] = []

        # Prochaine deadline critique
        upcoming_critical = [
            dl for dl in self._deadlines
            if dl.priority == Priority.CRITIQUE and dl.days_remaining <= 7
        ]
        if upcoming_critical:
            names = ", ".join(f"'{dl.title}'" for dl in upcoming_critical[:2])
            recs.append(
                f"🎯 Priorité absolue cette semaine : {names}. "
                "Alloue au moins 2h/jour jusqu'à la remise."
            )

        # Deadlines sans heures estimées
        no_estimate = [dl for dl in self._deadlines if dl.estimated_hours == 0]
        if no_estimate:
            recs.append(
                f"⏱️ {len(no_estimate)} deadline(s) sans estimation de temps. "
                "Édite-les et ajoute une estimation pour une analyse plus précise."
            )

        # Surcharge horaire
        if total_hours > 40:
            recs.append(
                f"📊 Charge totale estimée : {total_hours:.0f}h. C'est beaucoup ! "
                "Envisage de négocier une extension sur les travaux moins critiques."
            )

        # Planning anticipé
        if rush_weeks:
            week_count = len(rush_weeks)
            recs.append(
                f"📅 {week_count} semaine(s) de rush détectée(s). "
                "Conseil: commence la semaine précédente et travaille en tranches de 45min "
                "(technique Pomodoro → Tomate timer = ton nouveau meilleur ami)."
            )

        # Stratégie par priorité
        high_priority = [
            dl for dl in self._deadlines
            if dl.priority in (Priority.ELEVE, Priority.CRITIQUE)
        ]
        if len(high_priority) > 3:
            recs.append(
                f"🔥 Tu as {len(high_priority)} tâches haute priorité. "
                "Utilise la méthode MoSCoW : 'Must have' d'abord, "
                "le reste seulement si le temps le permet."
            )

        # Conseil bien-être
        if global_stress > 60:
            recs.append(
                "💆 Rappel bien-être ICHEC : 8h de sommeil restent non-négociables. "
                "Un esprit reposé est 40% plus efficace (c'est prouvé, et pas qu'à Montgomery)."
            )

        # Si tout va bien
        if not recs:
            recs.append(
                "✅ Ton organisation semble bonne ! "
                "Continue à mettre à jour tes deadlines régulièrement "
                "pour que l'IA reste pertinente."
            )

        return recs

    def _generate_advice_summary(
        self,
        global_stress: int,
        rush_weeks:    List[str],
        total_hours:   float,
    ) -> str:
        """
        Génère un paragraphe de synthèse style 'Rapport IA personnalisé'.
        Simule le rendu d'un LLM avec des templates dynamiques.
        """
        today_str   = date.today().strftime("%d/%m/%Y")
        nb_active   = len(self._deadlines)
        nb_rush     = len(rush_weeks)

        if nb_active == 0:
            return (
                f"📊 **Analyse IA DeadlineMap — {today_str}**\n\n"
                "Aucune deadline active détectée. Ton tableau de bord est vide. "
                "C'est soit très bien (tout est rendu !), soit inquiétant "
                "(as-tu vraiment vérifié ton Moodle ICHEC aujourd'hui ?)."
            )

        stress_context = {
            range(0,  20): "La situation est globalement sous contrôle.",
            range(20, 40): "La charge est légère mais mérite attention.",
            range(40, 60): "La pression monte. Il est temps de s'organiser sérieusement.",
            range(60, 80): "La charge est significative. Mode concentration activé recommandé.",
            range(80, 101): "ALERTE MAXIMALE. Réorganise ton planning d'urgence.",
        }

        context_msg = "La situation nécessite ton attention."
        for score_range, msg in stress_context.items():
            if global_stress in score_range:
                context_msg = msg
                break

        rush_msg = (
            f"L'analyse temporelle identifie {nb_rush} semaine(s) à risque élevé "
            f"({', '.join(rush_weeks)}). "
            if nb_rush else
            "Aucun cluster de deadlines simultanées détecté cette période. "
        )

        hours_msg = (
            f"La charge de travail totale estimée est de {total_hours:.1f} heures. "
            if total_hours > 0 else
            "Aucune estimation de temps saisie (pense à les renseigner !). "
        )

        return (
            f"📊 **Analyse IA DeadlineMap — {today_str}**\n\n"
            f"J'ai analysé tes {nb_active} deadline(s) active(s). "
            f"{context_msg} "
            f"Score de stress global : **{global_stress}/100**. "
            f"\n\n{rush_msg}"
            f"{hours_msg}"
            f"\n\nConsulte les recommandations ci-dessous pour optimiser ton planning. "
            f"— *DeadlineMap IA, service de conseil académique virtuel de l'ICHEC* 🎓"
        )
