from django.conf import settings
from django.db import models


class Nest(models.Model):

    class Status(models.TextChoices):
        PENDING  = 'pending',  'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    name        = models.CharField(max_length=255)
    description = models.TextField()
    creator     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    members     = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='NestMembership',
        related_name='nests',
    )
    status      = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    # --- permission helpers ---

    def membership_for(self, user):
        """Return the active NestMembership for this user in this nest, or None."""
        if not getattr(user, 'is_authenticated', False):
            return None
        return self.memberships.filter(user=user, status=NestMembership.Status.ACTIVE).first()

    def is_site_staff(self, user):
        """True if the user has site-wide staff or superuser rights."""
        return bool(getattr(user, 'is_authenticated', False) and (user.is_staff or user.is_superuser))

    def is_nest_staff(self, user):
        """True if the user is an instructor or assistant in this nest."""
        m = self.membership_for(user)
        return m is not None and m.role in (NestMembership.Role.INSTRUCTOR, NestMembership.Role.ASSISTANT)

    def is_member(self, user):
        """True if the user has any active membership in this nest."""
        return self.membership_for(user) is not None


class NestMembership(models.Model):
    """Represents a user's role and standing inside a specific Nest."""

    class Role(models.TextChoices):
        INSTRUCTOR = 'instructor', 'Instructor'
        ASSISTANT  = 'assistant',  'Assistant'
        MEMBER     = 'member',     'Member'

    class Status(models.TextChoices):
        PENDING  = 'pending',  'Pending'
        ACTIVE   = 'active',   'Active'
        REJECTED = 'rejected', 'Rejected'

    nest      = models.ForeignKey(Nest, on_delete=models.CASCADE, related_name='memberships')
    user      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='nest_memberships')
    role      = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    status    = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['nest', 'user'], name='unique_nest_membership')
        ]
        ordering = ['nest', 'joined_at']

    def __str__(self):
        return f'{self.user} → {self.nest} ({self.get_role_display()}, {self.get_status_display()})'