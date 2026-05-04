from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessments', '0003_assessment_nest'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        'ALTER TABLE assessments_assessment '
                        'ADD COLUMN IF NOT EXISTS duration integer NOT NULL DEFAULT 0;'
                    ),
                    reverse_sql=(
                        'ALTER TABLE assessments_assessment '
                        'DROP COLUMN IF EXISTS duration;'
                    ),
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='assessment',
                    name='duration',
                    field=models.PositiveIntegerField(
                        default=0,
                        help_text='Duration in minutes (0 = no time limit)',
                    ),
                ),
            ],
        ),
    ]
