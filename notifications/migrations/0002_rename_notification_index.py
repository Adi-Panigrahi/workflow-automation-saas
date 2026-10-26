from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0001_initial"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="notification",
            old_name="notification_recipient_read_created_idx",
            new_name="notif_recipient_read_created",
        ),
    ]
