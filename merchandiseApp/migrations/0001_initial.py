# Generated manual migration for merchandiseApp 0001_initial
from django.db import migrations, models
import uuid
from django.conf import settings

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Merchandise',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('name', models.CharField(max_length=255)),
                ('price', models.IntegerField()),
                ('category', models.CharField(max_length=100)),
                ('stock', models.IntegerField()),
                ('sold', models.IntegerField(default=0)),
                ('thumbnail', models.URLField(blank=True, null=True)),
                ('description', models.TextField()),
                ('user', models.ForeignKey(null=True, on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
