import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='movie',
            name='genre',
            field=models.CharField(
                choices=[
                    ('action', 'Action'), ('comedy', 'Comedy'), ('drama', 'Drama'),
                    ('horror', 'Horror'), ('romance', 'Romance'), ('thriller', 'Thriller'),
                    ('sci_fi', 'Sci-Fi'), ('animation', 'Animation'),
                    ('documentary', 'Documentary'), ('fantasy', 'Fantasy'),
                    ('adventure', 'Adventure'), ('biography', 'Biography'),
                ],
                default='action',
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name='movie',
            name='language',
            field=models.CharField(
                choices=[
                    ('english', 'English'), ('hindi', 'Hindi'), ('tamil', 'Tamil'),
                    ('telugu', 'Telugu'), ('kannada', 'Kannada'),
                    ('malayalam', 'Malayalam'), ('bengali', 'Bengali'),
                    ('marathi', 'Marathi'),
                ],
                default='hindi',
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name='movie',
            name='release_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='movie',
            name='price',
            field=models.DecimalField(decimal_places=2, default=200.0, max_digits=8),
        ),
        migrations.AddField(
            model_name='theater',
            name='city',
            field=models.CharField(
                choices=[
                    ('mumbai', 'Mumbai'), ('delhi', 'Delhi'), ('bangalore', 'Bangalore'),
                    ('chennai', 'Chennai'), ('hyderabad', 'Hyderabad'),
                    ('kolkata', 'Kolkata'), ('pune', 'Pune'), ('ahmedabad', 'Ahmedabad'),
                    ('jaipur', 'Jaipur'), ('surat', 'Surat'),
                ],
                default='mumbai',
                max_length=50,
            ),
        ),
        migrations.CreateModel(
            name='MovieView',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(blank=True, max_length=40, null=True)),
                ('viewed_at', models.DateTimeField(auto_now_add=True)),
                ('movie', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='views',
                    to='movies.movie',
                )),
                ('user', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'ordering': ['-viewed_at']},
        ),
    ]
