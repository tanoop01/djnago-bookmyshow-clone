import uuid
from django.db import migrations, models


def populate_booking_ids(apps, schema_editor):
    Booking = apps.get_model('movies', 'Booking')
    for booking in Booking.objects.all():
        if not booking.booking_id:
            booking.booking_id = f"BMS-{uuid.uuid4().hex[:8].upper()}"
        if not booking.payment_reference:
            booking.payment_reference = f"PAY-{uuid.uuid4().hex[:12].upper()}"
        booking.save()


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0002_movie_discovery_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='theater',
            name='screen',
            field=models.CharField(default='Screen 1', max_length=50),
        ),
        migrations.AddField(
            model_name='booking',
            name='payment_reference',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='booking',
            name='booking_id',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.RunPython(populate_booking_ids, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='booking',
            name='booking_id',
            field=models.CharField(blank=True, max_length=50, unique=True),
        ),
    ]
