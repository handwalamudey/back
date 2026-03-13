from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0002_voter_opted_in_message'),
    ]

    operations = [
        migrations.AddField(
            model_name='voter',
            name='tribe',
            field=models.CharField(max_length=100, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='voter',
            name='ward',
            field=models.CharField(max_length=100, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='voter',
            name='polling_center',
            field=models.CharField(max_length=255, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='voter',
            name='stream',
            field=models.CharField(max_length=100, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='voter',
            name='mobilized_by',
            field=models.CharField(max_length=255, blank=True, null=True),
        ),
    ]


