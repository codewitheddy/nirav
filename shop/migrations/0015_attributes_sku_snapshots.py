"""
Migration 0015 — Dynamic Attribute System + SKU + Snapshots

Adds:
  - Attribute       (product-scoped attribute type, e.g. "Color")
  - AttributeValue  (concrete value, e.g. "Red")
  - VariantAttributeValue  (many-to-many link: variant ↔ attribute value)
  - ProductVariant.sku            (unique, nullable)
  - ProductVariant.cost_price     (nullable)
  - ProductVariant.weight         (nullable)
  - OrderItem.variant_name        (snapshot)
  - OrderItem.sku_snapshot        (snapshot)
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0014_product_variant_stock'),
    ]

    operations = [
        # ── Attribute ──────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='Attribute',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100,
                                          help_text="e.g. Color, Size, Material")),
                ('position', models.PositiveSmallIntegerField(
                    default=0, help_text='Display order')),
                ('product', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attributes',
                    to='shop.product',
                )),
            ],
            options={
                'ordering': ['position', 'id'],
            },
        ),
        migrations.AddConstraint(
            model_name='attribute',
            constraint=models.UniqueConstraint(
                fields=['product', 'name'],
                name='unique_attribute_per_product',
            ),
        ),

        # ── AttributeValue ────────────────────────────────────────────────────
        migrations.CreateModel(
            name='AttributeValue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=100)),
                ('position', models.PositiveSmallIntegerField(default=0)),
                ('attribute', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='values',
                    to='shop.attribute',
                )),
            ],
            options={
                'ordering': ['position', 'id'],
            },
        ),
        migrations.AddConstraint(
            model_name='attributevalue',
            constraint=models.UniqueConstraint(
                fields=['attribute', 'value'],
                name='unique_value_per_attribute',
            ),
        ),

        # ── VariantAttributeValue ─────────────────────────────────────────────
        migrations.CreateModel(
            name='VariantAttributeValue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('attribute_value', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='variant_links',
                    to='shop.attributevalue',
                )),
                ('variant', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attribute_values',
                    to='shop.productvariant',
                )),
            ],
        ),
        migrations.AddConstraint(
            model_name='variantattributevalue',
            constraint=models.UniqueConstraint(
                fields=['variant', 'attribute_value'],
                name='unique_variant_attribute_value',
            ),
        ),

        # ── ProductVariant new fields ─────────────────────────────────────────
        migrations.AddField(
            model_name='productvariant',
            name='sku',
            field=models.CharField(
                blank=True, max_length=100, null=True, unique=True,
                help_text='Stock-keeping unit — must be unique across all variants',
            ),
        ),
        migrations.AddField(
            model_name='productvariant',
            name='cost_price',
            field=models.DecimalField(
                decimal_places=2, max_digits=10, null=True, blank=True,
                help_text='Internal cost price (not shown to customers)',
            ),
        ),
        migrations.AddField(
            model_name='productvariant',
            name='weight',
            field=models.DecimalField(
                decimal_places=3, max_digits=8, null=True, blank=True,
                help_text='Weight in kg (optional)',
            ),
        ),

        # ── OrderItem snapshot fields ─────────────────────────────────────────
        migrations.AddField(
            model_name='orderitem',
            name='variant_name',
            field=models.CharField(
                blank=True, default='', max_length=200,
                help_text='Variant display name at time of order',
            ),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='sku_snapshot',
            field=models.CharField(
                blank=True, default='', max_length=100,
                help_text='SKU at time of order',
            ),
        ),
    ]
