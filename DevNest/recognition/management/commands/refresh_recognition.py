"""
Management command: refresh_recognition

Usage:
    python manage.py refresh_recognition          # all approved nests
    python manage.py refresh_recognition --nest 1 # specific nest by pk
"""
from django.core.management.base import BaseCommand
from nests.models import Nest
from recognition.engine import refresh_recognition_for_nest, refresh_recognition


class Command(BaseCommand):
    help = 'Recompute title and badge for all members in approved nests.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--nest', type=int, default=None,
            help='Limit refresh to a specific nest pk.'
        )

    def handle(self, *args, **options):
        nest_pk = options['nest']
        if nest_pk:
            try:
                nest = Nest.objects.get(pk=nest_pk)
            except Nest.DoesNotExist:
                self.stderr.write(self.style.ERROR(f'Nest {nest_pk} not found.'))
                return
            nests = [nest]
        else:
            nests = list(Nest.objects.filter(status=Nest.Status.APPROVED))

        total = 0
        for nest in nests:
            refresh_recognition_for_nest(nest)
            count = nest.recognitions.count()
            total += count
            self.stdout.write(f'  {nest.name}: {count} member(s) refreshed')

        self.stdout.write(self.style.SUCCESS(
            f'Done. Refreshed recognition for {total} user-nest pair(s) across {len(nests)} nest(s).'
        ))
