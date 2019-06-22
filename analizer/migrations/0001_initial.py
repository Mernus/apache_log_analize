# Generated by Django 2.2.2 on 2019-06-19 16:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Logfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('log_url', models.URLField()),
                ('added_datetime', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Logdata',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime', models.DateTimeField()),
                ('ip', models.GenericIPAddressField(unpack_ipv4=True)),
                ('http_method', models.CharField(max_length=7)),
                ('requested_path', models.CharField(max_length=300)),
                ('http_protocol', models.CharField(max_length=9)),
                ('status_code', models.PositiveSmallIntegerField()),
                ('size_requested_obj', models.CharField(max_length=20)),
                ('referer', models.CharField(max_length=300)),
                ('logfile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='analizer.Logfile')),
            ],
        ),
    ]
