from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0015_attributes_sku_snapshots'),
    ]

    operations = [
        migrations.AddField(
            model_name='herobanner',
            name='pill_1_icon_custom',
            field=models.CharField(
                blank=True, default='', max_length=1000,
                help_text='SVG <path> content when icon is set to Custom',
            ),
        ),
        migrations.AddField(
            model_name='herobanner',
            name='pill_2_icon_custom',
            field=models.CharField(
                blank=True, default='', max_length=1000,
                help_text='SVG <path> content when icon is set to Custom',
            ),
        ),
        migrations.AddField(
            model_name='herobanner',
            name='pill_3_icon_custom',
            field=models.CharField(
                blank=True, default='', max_length=1000,
                help_text='SVG <path> content when icon is set to Custom',
            ),
        ),
        migrations.AlterField(
            model_name='herobanner',
            name='pill_1_icon',
            field=models.CharField(
                blank=True, default='shield', max_length=20,
                choices=[
                    ('check', '✓ Checkmark'), ('shield', '🛡 Shield'),
                    ('star', '★ Star'), ('heart', '♥ Heart'),
                    ('leaf', '🌿 Leaf'), ('diamond', '◆ Diamond'),
                    ('droplet', '💧 Droplet'), ('circle', '○ Circle'),
                    ('custom', '✏ Custom SVG path'),
                ],
            ),
        ),
        migrations.AlterField(
            model_name='herobanner',
            name='pill_2_icon',
            field=models.CharField(
                blank=True, default='droplet', max_length=20,
                choices=[
                    ('check', '✓ Checkmark'), ('shield', '🛡 Shield'),
                    ('star', '★ Star'), ('heart', '♥ Heart'),
                    ('leaf', '🌿 Leaf'), ('diamond', '◆ Diamond'),
                    ('droplet', '💧 Droplet'), ('circle', '○ Circle'),
                    ('custom', '✏ Custom SVG path'),
                ],
            ),
        ),
        migrations.AlterField(
            model_name='herobanner',
            name='pill_3_icon',
            field=models.CharField(
                blank=True, default='check', max_length=20,
                choices=[
                    ('check', '✓ Checkmark'), ('shield', '🛡 Shield'),
                    ('star', '★ Star'), ('heart', '♥ Heart'),
                    ('leaf', '🌿 Leaf'), ('diamond', '◆ Diamond'),
                    ('droplet', '💧 Droplet'), ('circle', '○ Circle'),
                    ('custom', '✏ Custom SVG path'),
                ],
            ),
        ),
    ]
