from django.db import models
from django.contrib.auth.models import User
from nests.models import Nest


# ── Title tiers (ordered by threshold ascending) ──────────────────────────────
TITLE_TIERS = [
    (0,    "New Member"),
    (5,    "Explorer"),
    (15,   "Contributor"),
    (30,   "Active Contributor"),
    (50,   "Engaged Member"),
    (75,   "Top Contributor"),
    (100,  "Advanced Contributor"),
    (150,  "Core Member"),
    (200,  "Mentor"),
    (300,  "Senior Mentor"),
    (450,  "Knowledge Leader"),
    (600,  "Nest Expert"),
    (800,  "Master Contributor"),
    (1000, "Pillar of the Nest"),
]

TITLE_CHOICES = [(name, name) for _, name in TITLE_TIERS]


# ── Badge options ─────────────────────────────────────────────────────────────
BADGE_CHOICES = [
    ("",                   "—"),
    ("First Responder",    "First Responder"),
    ("Rapid Helper",       "Rapid Helper"),
    ("Problem Solver",     "Problem Solver"),
    ("Verified Expert",    "Verified Expert"),
    ("Precision Thinker",  "Precision Thinker"),
    ("Curious Mind",       "Curious Mind"),
    ("Explorer",           "Explorer"),
    ("Collaborator",       "Collaborator"),
    ("Discussion Starter", "Discussion Starter"),
    ("Community Builder",  "Community Builder"),
    ("Influencer",         "Influencer"),
    ("Insightful Voice",   "Insightful Voice"),
]

BADGE_ICONS = {
    "First Responder":    "bi-lightning-charge-fill",
    "Rapid Helper":       "bi-lightning-fill",
    "Problem Solver":     "bi-check2-circle",
    "Verified Expert":    "bi-patch-check-fill",
    "Precision Thinker":  "bi-bullseye",
    "Curious Mind":       "bi-question-circle-fill",
    "Explorer":           "bi-compass-fill",
    "Collaborator":       "bi-people-fill",
    "Discussion Starter": "bi-chat-dots-fill",
    "Community Builder":  "bi-heart-fill",
    "Influencer":         "bi-megaphone-fill",
    "Insightful Voice":   "bi-lightbulb-fill",
}


def score_to_title(score: int) -> str:
    """Return the highest title tier the score qualifies for."""
    title = TITLE_TIERS[0][1]
    for threshold, name in TITLE_TIERS:
        if score >= threshold:
            title = name
        else:
            break
    return title


class NestRecognition(models.Model):
    """Stores a user's computed title and badge within a specific Nest."""

    user         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recognitions')
    nest         = models.ForeignKey(Nest, on_delete=models.CASCADE, related_name='recognitions')
    score        = models.IntegerField(default=0)
    title        = models.CharField(max_length=64, choices=TITLE_CHOICES, default="New Member")
    badge        = models.CharField(max_length=64, choices=BADGE_CHOICES, blank=True, default="")
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('user', 'nest')]
        ordering = ['-score']

    def __str__(self):
        return f'{self.user.username} in {self.nest.name}: {self.title} / {self.badge or "no badge"}'

    @property
    def badge_icon(self):
        return BADGE_ICONS.get(self.badge, "bi-award")
