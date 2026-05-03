"""
Django signals that trigger recognition refresh whenever relevant activity
(posts, comments, votes) changes inside a nest.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


def _refresh(user, nest):
    if nest is None:
        return
    from recognition.engine import refresh_recognition
    try:
        refresh_recognition(user, nest)
    except Exception:
        pass  # never let recognition errors crash a request


# ── Post saved / deleted ──────────────────────────────────────────────────────
@receiver(post_save, sender='posts.Post')
def on_post_save(sender, instance, **kwargs):
    _refresh(instance.user, instance.nest)


@receiver(post_delete, sender='posts.Post')
def on_post_delete(sender, instance, **kwargs):
    _refresh(instance.user, instance.nest)


# ── Comment saved / deleted ───────────────────────────────────────────────────
@receiver(post_save, sender='posts.Comment')
def on_comment_save(sender, instance, **kwargs):
    _refresh(instance.user, instance.post.nest)


@receiver(post_delete, sender='posts.Comment')
def on_comment_delete(sender, instance, **kwargs):
    _refresh(instance.user, instance.post.nest)


# ── Vote saved / deleted ──────────────────────────────────────────────────────
@receiver(post_save, sender='posts.PostVote')
def on_vote_save(sender, instance, **kwargs):
    # Refresh the post's *author* since upvotes affect their score
    _refresh(instance.post.user, instance.post.nest)


@receiver(post_delete, sender='posts.PostVote')
def on_vote_delete(sender, instance, **kwargs):
    _refresh(instance.post.user, instance.post.nest)
