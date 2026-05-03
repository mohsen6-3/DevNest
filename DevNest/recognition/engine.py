"""
Recognition scoring engine.

All scoring is per (user, nest).  Call ``refresh_recognition(user, nest)`` to
recompute and persist a NestRecognition row.
"""
from __future__ import annotations

import datetime
from django.db.models import Count, Sum, Q
from django.utils import timezone


# ── Scoring weights ───────────────────────────────────────────────────────────
W_POST          = 2   # per post created in the nest
W_COMMENT       = 1   # per comment written (not own posts)
W_UPVOTE_RECV   = 3   # per net upvote received on posts
W_VERIFIED      = 5   # per verified / approved comment

# Badge category weights (used to pick dominant category)
W_EARLY_COMMENT = 8   # response within 2 h of post creation
W_VERIFIED_ANS  = 10  # verified comment
W_QUESTION_POST = 6   # question post that got at least one reply
W_INFLUENCE     = 4   # net upvote on a post (same as above but separate bucket)
W_DISCUSSION    = 5   # a post authored by user with ≥ 2 comments (not by author)
W_COLLAB        = 2   # plain comment on someone else's post

EARLY_HOURS = 2  # how many hours counts as "early"


def _compute_scores(user, nest) -> dict:
    """Return raw activity metrics for (user, nest)."""
    from posts.models import Post, Comment, PostVote

    nest_posts = Post.objects.filter(nest=nest)
    user_posts = nest_posts.filter(user=user)

    post_ids     = list(user_posts.values_list('id', flat=True))
    all_post_ids = list(nest_posts.values_list('id', flat=True))

    # -- Contribution score components
    post_count = user_posts.count()

    comment_count = Comment.objects.filter(
        user=user, post__in=all_post_ids
    ).exclude(post__user=user).count()  # exclude commenting on own posts

    net_upvotes = (
        PostVote.objects.filter(post__in=post_ids)
        .aggregate(total=Sum('value'))['total'] or 0
    )
    net_upvotes = max(net_upvotes, 0)  # clamp to 0 — don't penalise score

    verified_count = Comment.objects.filter(
        user=user, post__in=all_post_ids, is_verified=True
    ).count()

    score = (
        post_count * W_POST
        + comment_count * W_COMMENT
        + net_upvotes * W_UPVOTE_RECV
        + verified_count * W_VERIFIED
    )

    # -- Badge category scores
    cutoff = timezone.now() - datetime.timedelta(hours=EARLY_HOURS)

    # Pure-Python approach — works on SQLite and all other backends
    early_comment_score = 0
    for c in Comment.objects.filter(user=user, post__nest=nest).select_related('post'):
        delta = c.created_at - c.post.created_at
        if 0 <= delta.total_seconds() <= EARLY_HOURS * 3600:
            early_comment_score += 1

    verified_ans_score = verified_count

    question_type_ids = list(
        Post.objects.filter(nest=nest, user=user, post_type__name__iexact='question')
        .annotate(reply_count=Count('comments'))
        .filter(reply_count__gt=0)
        .values_list('id', flat=True)
    )
    question_post_score = len(question_type_ids)

    discussion_score = (
        Post.objects.filter(nest=nest, user=user)
        .annotate(
            ext_comments=Count('comments', filter=~Q(comments__user=user))
        )
        .filter(ext_comments__gte=2)
        .count()
    )

    collab_score = comment_count  # comments on other people's posts

    return {
        'score': score,
        # badge category raw scores
        'speed':        early_comment_score * W_EARLY_COMMENT,
        'accuracy':     verified_ans_score  * W_VERIFIED_ANS,
        'curiosity':    question_post_score * W_QUESTION_POST,
        'influence':    net_upvotes         * W_INFLUENCE,
        'discussion':   discussion_score    * W_DISCUSSION,
        'collaboration': collab_score       * W_COLLAB,
    }


# Badge selection: category → badge name
_CATEGORY_BADGE = {
    'speed':        'First Responder',
    'accuracy':     'Problem Solver',
    'curiosity':    'Curious Mind',
    'influence':    'Influencer',
    'discussion':   'Discussion Starter',
    'collaboration':'Collaborator',
}


def _pick_badge(metrics: dict) -> str:
    """Return the badge name for the dominant category, or '' if no activity."""
    categories = {k: metrics[k] for k in _CATEGORY_BADGE}
    best_cat, best_val = max(categories.items(), key=lambda x: x[1])
    if best_val == 0:
        return ''
    return _CATEGORY_BADGE[best_cat]


def refresh_recognition(user, nest) -> 'NestRecognition':  # type: ignore[name-defined]
    """Recompute and save the NestRecognition for (user, nest). Returns the instance."""
    from recognition.models import NestRecognition, score_to_title

    metrics = _compute_scores(user, nest)
    title   = score_to_title(metrics['score'])
    badge   = _pick_badge(metrics)

    obj, _ = NestRecognition.objects.get_or_create(user=user, nest=nest)
    obj.score = metrics['score']
    obj.title = title
    obj.badge = badge
    obj.save()
    return obj


def refresh_recognition_for_nest(nest) -> None:
    """Recompute recognition for every active member of a nest."""
    from nests.models import NestMembership
    members = (
        NestMembership.objects
        .filter(nest=nest, status=NestMembership.Status.ACTIVE)
        .select_related('user')
    )
    for m in members:
        refresh_recognition(m.user, nest)
