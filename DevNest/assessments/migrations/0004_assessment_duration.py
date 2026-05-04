# Generated migration for adding duration field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessments', '0003_assessment_nest'),
    ]

    operations = [
        migrations.AddField(
            model_name='assessment',
            name='duration',
            field=models.PositiveIntegerField(default=0, help_text='Duration in minutes (0 = no time limit)'),
        ),
    ]
