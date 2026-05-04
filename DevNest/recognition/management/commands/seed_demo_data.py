from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from assessments.models import Answer, Assessment, Choice, Question, Submission
from content.models import LinkContent, TextContent, Title, Topic, Unit
from main.models import Notification
from nests.models import Nest, NestMembership
from posts.models import (
    Comment,
    Post,
    PostReadStatus,
    PostSubscription,
    PostTag,
    PostType,
    PostVote,
)
from recognition.models import NestRecognition


class Command(BaseCommand):
    help = "Seed light but effective demo data with old/new timelines."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Clear existing demo-related data before seeding.",
        )

    @staticmethod
    def _set_dt(obj, field, dt):
        obj.__class__.objects.filter(pk=obj.pk).update(**{field: dt})

    def _reset_data(self):
        User = get_user_model()

        # Delete app data in a safe order while preserving superusers.
        Notification.objects.all().delete()

        Answer.objects.all().delete()
        Submission.objects.all().delete()
        Choice.objects.all().delete()
        Question.objects.all().delete()
        Assessment.objects.all().delete()

        LinkContent.objects.all().delete()
        TextContent.objects.all().delete()
        Topic.objects.all().delete()
        Unit.objects.all().delete()
        Title.objects.all().delete()

        Comment.objects.all().delete()
        PostVote.objects.all().delete()
        PostReadStatus.objects.all().delete()
        PostSubscription.objects.all().delete()
        Post.objects.all().delete()
        PostTag.objects.all().delete()
        PostType.objects.all().delete()

        NestRecognition.objects.all().delete()
        NestMembership.objects.all().delete()
        Nest.objects.all().delete()

        User.objects.filter(is_superuser=False).delete()

    def handle(self, *args, **options):
        now = timezone.now()

        with transaction.atomic():
            if options["reset"]:
                self._reset_data()
                self.stdout.write(self.style.WARNING("Existing demo data reset complete."))

            User = get_user_model()

            # --- Users ---
            users_data = [
                ("instructor_ali", "Ali", "Hassan", "ali@devnest.demo", False, False),
                ("assistant_noor", "Noor", "Saad", "noor@devnest.demo", False, False),
                ("student_omar", "Omar", "Khalid", "omar@devnest.demo", False, False),
                ("student_sara", "Sara", "Fahad", "sara@devnest.demo", False, False),
                ("student_lina", "Lina", "Saif", "lina@devnest.demo", False, False),
                ("student_hamad", "Hamad", "Nasser", "hamad@devnest.demo", False, False),
                ("site_staff", "Site", "Staff", "staff@devnest.demo", True, False),
            ]

            users = {}
            for username, first_name, last_name, email, is_staff, is_superuser in users_data:
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email,
                        "is_staff": is_staff,
                        "is_superuser": is_superuser,
                    },
                )
                if created:
                    user.set_password("DemoPass123!")
                    user.save(update_fields=["password"])
                users[username] = user

            # --- Nests ---
            nest_python, _ = Nest.objects.get_or_create(
                name="CS101 - Python Foundations",
                defaults={
                    "description": "Core Python, loops, functions, and practical exercises.",
                    "creator": users["instructor_ali"],
                    "status": Nest.Status.APPROVED,
                },
            )
            nest_ds, _ = Nest.objects.get_or_create(
                name="Data Structures Bootcamp",
                defaults={
                    "description": "Arrays, linked lists, trees, and complexity practice.",
                    "creator": users["instructor_ali"],
                    "status": Nest.Status.APPROVED,
                },
            )
            nest_pending, _ = Nest.objects.get_or_create(
                name="AI Fundamentals (Summer)",
                defaults={
                    "description": "Proposed nest for summer intro to AI and ML basics.",
                    "creator": users["student_sara"],
                    "status": Nest.Status.PENDING,
                },
            )

            self._set_dt(nest_python, "created_at", now - timedelta(days=95))
            self._set_dt(nest_ds, "created_at", now - timedelta(days=38))
            self._set_dt(nest_pending, "created_at", now - timedelta(days=2))

            memberships = [
                (nest_python, "instructor_ali", NestMembership.Role.INSTRUCTOR, NestMembership.Status.ACTIVE, 94),
                (nest_python, "assistant_noor", NestMembership.Role.ASSISTANT, NestMembership.Status.ACTIVE, 80),
                (nest_python, "student_omar", NestMembership.Role.MEMBER, NestMembership.Status.ACTIVE, 60),
                (nest_python, "student_sara", NestMembership.Role.MEMBER, NestMembership.Status.ACTIVE, 40),
                (nest_python, "student_lina", NestMembership.Role.MEMBER, NestMembership.Status.PENDING, 1),

                (nest_ds, "instructor_ali", NestMembership.Role.INSTRUCTOR, NestMembership.Status.ACTIVE, 37),
                (nest_ds, "assistant_noor", NestMembership.Role.ASSISTANT, NestMembership.Status.ACTIVE, 32),
                (nest_ds, "student_hamad", NestMembership.Role.MEMBER, NestMembership.Status.ACTIVE, 21),
                (nest_ds, "student_omar", NestMembership.Role.MEMBER, NestMembership.Status.ACTIVE, 15),
            ]

            for nest, username, role, status, days_ago in memberships:
                membership, _ = NestMembership.objects.get_or_create(
                    nest=nest,
                    user=users[username],
                    defaults={"role": role, "status": status},
                )
                membership.role = role
                membership.status = status
                membership.save(update_fields=["role", "status"])
                self._set_dt(membership, "joined_at", now - timedelta(days=days_ago))

            # --- Post types & tags ---
            pt_question, _ = PostType.objects.get_or_create(name="Question")
            pt_discussion, _ = PostType.objects.get_or_create(name="Discussion")
            pt_announcement, _ = PostType.objects.get_or_create(name="Announcement")

            tags = {}
            for tag_name in ["python", "loops", "functions", "exam-prep", "arrays", "trees"]:
                tag, _ = PostTag.objects.get_or_create(name=tag_name)
                tags[tag_name] = tag

            # --- Posts (old -> new spread) ---
            posts = []
            posts_data = [
                (nest_python, "instructor_ali", "Welcome to CS101", "Course roadmap and weekly structure.", pt_announcement, True, 90, ["exam-prep"]),
                (nest_python, "student_omar", "When should I use while vs for?", "I get confused choosing loops in practice problems.", pt_question, False, 28, ["python", "loops"]),
                (nest_python, "assistant_noor", "Function naming best practices", "Share naming patterns you use in assignments.", pt_discussion, False, 9, ["python", "functions"]),
                (nest_python, "student_sara", "Mock exam tips for week 8", "Can we share a checklist for debugging under time pressure?", pt_discussion, False, 2, ["exam-prep"]),
                (nest_python, "instructor_ali", "Lab moved to Thursday", "This week only: lab session moved due to campus event.", pt_announcement, True, 0, ["exam-prep"]),

                (nest_ds, "instructor_ali", "Bootcamp kickoff", "Start with arrays and two-pointer techniques.", pt_announcement, True, 35, ["arrays"]),
                (nest_ds, "student_hamad", "Tree traversal cheat sheet", "Posting my DFS/BFS summary. Feedback welcome.", pt_discussion, False, 6, ["trees"]),
                (nest_ds, "student_omar", "Big-O in nested loops", "Need intuition for O(n^2) vs O(n log n).", pt_question, False, 1, ["arrays", "exam-prep"]),
            ]

            for nest, username, title, content, post_type, pinned, days_ago, tag_names in posts_data:
                post, _ = Post.objects.get_or_create(
                    nest=nest,
                    user=users[username],
                    title=title,
                    defaults={"content": content, "post_type": post_type, "is_pinned": pinned},
                )
                post.content = content
                post.post_type = post_type
                post.is_pinned = pinned
                post.save(update_fields=["content", "post_type", "is_pinned"])
                post.tags.set([tags[name] for name in tag_names])

                ts = now - timedelta(days=days_ago, hours=(days_ago % 5) + 2)
                if days_ago == 0:
                    ts = now - timedelta(hours=3)
                self._set_dt(post, "created_at", ts)
                posts.append(post)

            # --- Comments and replies ---
            comments_data = [
                (posts[1], "assistant_noor", "Use `for` when you know iteration bounds; `while` for condition-driven loops.", None, 27),
                (posts[1], "student_sara", "Try both on a small input and inspect variable changes.", None, 26),
                (posts[2], "student_omar", "I prefer verb_noun style like `calculate_score`.", None, 8),
                (posts[3], "instructor_ali", "Great topic. I will post a sample rubric tonight.", None, 1),
                (posts[6], "assistant_noor", "Nice summary. Add preorder/inorder examples.", None, 5),
                (posts[7], "instructor_ali", "We will practice this in tomorrow's session.", None, 0),
            ]

            created_comments = []
            for post, username, content, parent, days_ago in comments_data:
                comment, _ = Comment.objects.get_or_create(
                    post=post,
                    user=users[username],
                    content=content,
                    parent=parent,
                    defaults={"approved": True, "is_verified": False},
                )
                comment.approved = True
                comment.is_verified = users[username] == users["instructor_ali"]
                comment.save(update_fields=["approved", "is_verified"])
                self._set_dt(comment, "created_at", now - timedelta(days=days_ago, hours=1))
                created_comments.append(comment)

            # Add one reply chain for demo
            reply, _ = Comment.objects.get_or_create(
                post=posts[1],
                user=users["student_omar"],
                parent=created_comments[0],
                content="That distinction makes sense now, thanks!",
                defaults={"approved": True, "is_verified": False},
            )
            self._set_dt(reply, "created_at", now - timedelta(days=26, hours=6))

            # --- Votes ---
            votes_data = [
                (posts[1], "assistant_noor", 1),
                (posts[1], "student_sara", 1),
                (posts[2], "student_omar", 1),
                (posts[2], "student_sara", 1),
                (posts[6], "instructor_ali", 1),
                (posts[7], "assistant_noor", 1),
                (posts[7], "student_hamad", 1),
            ]
            for post, username, value in votes_data:
                vote, _ = PostVote.objects.get_or_create(post=post, user=users[username], defaults={"value": value})
                vote.value = value
                vote.save(update_fields=["value"])

            # --- Subscriptions / read status ---
            for post in posts:
                for username in ["student_omar", "student_sara", "student_hamad"]:
                    if post.nest == nest_python and username == "student_hamad":
                        continue
                    sub, _ = PostSubscription.objects.get_or_create(post=post, user=users[username])
                    sub.is_enabled = True
                    sub.save(update_fields=["is_enabled"])

            # Mark old posts as read for one student; keep newer ones unread for demo
            for post in posts:
                if (now - post.created_at).days >= 7:
                    rs, _ = PostReadStatus.objects.get_or_create(post=post, user=users["student_omar"])
                    self._set_dt(rs, "read_at", now - timedelta(days=1))

            # --- Assessments ---
            quiz, _ = Assessment.objects.get_or_create(
                nest=nest_python,
                title="Quiz 1 - Python Basics",
                defaults={
                    "description": "Variables, loops, and functions.",
                    "assessment_type": "quiz",
                    "points": 20,
                    "due_date": now - timedelta(days=14),
                    "created_by": users["instructor_ali"],
                },
            )
            self._set_dt(quiz, "created_at", now - timedelta(days=30))

            assignment, _ = Assessment.objects.get_or_create(
                nest=nest_python,
                title="Assignment 2 - Practice Set",
                defaults={
                    "description": "Solve 5 short coding tasks with explanation.",
                    "assessment_type": "assignment",
                    "points": 40,
                    "due_date": now + timedelta(days=5),
                    "created_by": users["assistant_noor"],
                },
            )
            self._set_dt(assignment, "created_at", now - timedelta(days=3))

            q1, _ = Question.objects.get_or_create(
                assessment=quiz,
                text="Which loop is best when the number of iterations is known?",
                defaults={"question_type": "mcq", "points": 5},
            )
            q2, _ = Question.objects.get_or_create(
                assessment=quiz,
                text="Explain why functions improve maintainability.",
                defaults={"question_type": "text", "points": 5},
            )
            c1, _ = Choice.objects.get_or_create(question=q1, text="for loop", defaults={"is_correct": True})
            Choice.objects.get_or_create(question=q1, text="while loop", defaults={"is_correct": False})

            sub_omar, _ = Submission.objects.get_or_create(assessment=quiz, student=users["student_omar"], defaults={"score": 8})
            self._set_dt(sub_omar, "submitted_at", now - timedelta(days=13))
            Answer.objects.get_or_create(submission=sub_omar, question=q1, defaults={"selected_choice": c1, "is_correct": True})
            Answer.objects.get_or_create(submission=sub_omar, question=q2, defaults={"text_answer": "Functions remove duplication.", "is_correct": True})

            # --- Content ---
            title_py, _ = Title.objects.get_or_create(
                nest=nest_python,
                created_by=users["instructor_ali"],
                name="Week 1 - Python Essentials",
                defaults={"description": "Starter materials for week 1", "sort_order": 1, "is_published": True},
            )
            self._set_dt(title_py, "created_at", now - timedelta(days=32))

            unit_intro, _ = Unit.objects.get_or_create(
                title=title_py,
                name="Intro Unit",
                defaults={"description": "Getting started", "sort_order": 1, "is_published": True},
            )
            self._set_dt(unit_intro, "created_at", now - timedelta(days=31))

            topic_loops, _ = Topic.objects.get_or_create(
                unit=unit_intro,
                name="Loops and Control Flow",
                defaults={"sort_order": 1, "status": Topic.StatusChoices.PUBLISHED, "due_date": now - timedelta(days=20)},
            )
            self._set_dt(topic_loops, "created_at", now - timedelta(days=30))

            topic_functions, _ = Topic.objects.get_or_create(
                unit=unit_intro,
                name="Functions Deep Dive",
                defaults={"sort_order": 2, "status": Topic.StatusChoices.PUBLISHED, "due_date": now + timedelta(days=2)},
            )
            self._set_dt(topic_functions, "created_at", now - timedelta(days=4))

            TextContent.objects.get_or_create(
                topic=topic_loops,
                text_title="Loop Patterns Summary",
                defaults={"body": "Use for for bounded loops and while for condition-driven loops.", "format": "plain", "sort_order": 1},
            )
            LinkContent.objects.get_or_create(
                topic=topic_functions,
                display_text="Official Python docs: Defining Functions",
                defaults={"url": "https://docs.python.org/3/tutorial/controlflow.html#defining-functions", "sort_order": 1},
            )

            # --- Recognition snapshots ---
            rec_data = [
                ("student_omar", nest_python, 130, "Core Member", "Problem Solver"),
                ("student_sara", nest_python, 88, "Top Contributor", "Discussion Starter"),
                ("student_hamad", nest_ds, 64, "Engaged Member", "Collaborator"),
            ]
            for username, nest, score, title, badge in rec_data:
                rec, _ = NestRecognition.objects.get_or_create(user=users[username], nest=nest)
                rec.score = score
                rec.title = title
                rec.badge = badge
                rec.save(update_fields=["score", "title", "badge"])

            # --- Notifications (mix old/new + read/unread) ---
            notif_data = [
                ("student_omar", "Announcement: Lab moved to Thursday.", f"/nests/{nest_python.pk}/posts/", False, 0),
                ("student_omar", "New reply on your loop question.", f"/nests/{nest_python.pk}/posts/", False, 1),
                ("student_omar", "Quiz 1 score has been published.", f"/nests/{nest_python.pk}/assessments/", True, 12),
                ("student_sara", "Assignment 2 is due in 5 days.", f"/nests/{nest_python.pk}/assessments/", False, 0),
                ("student_hamad", "New discussion in Data Structures Bootcamp.", f"/nests/{nest_ds.pk}/posts/", True, 6),
            ]
            for username, message, link, is_read, days_ago in notif_data:
                notif, _ = Notification.objects.get_or_create(
                    user=users[username],
                    message=message,
                    defaults={"link": link, "is_read": is_read},
                )
                notif.link = link
                notif.is_read = is_read
                notif.save(update_fields=["link", "is_read"])
                self._set_dt(notif, "created_at", now - timedelta(days=days_ago, hours=2))

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))
        self.stdout.write("Demo users password: DemoPass123!")
        self.stdout.write("Suggested logins: instructor_ali, assistant_noor, student_omar, student_sara")
