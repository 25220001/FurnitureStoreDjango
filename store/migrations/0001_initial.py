# Generated by Django 5.2 on 2025-06-12 21:30

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Brand',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='brands/')),
                ('website', models.URLField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Color',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('hex_code', models.CharField(blank=True, help_text='Hex color code (e.g., #FF5733)', max_length=7)),
            ],
        ),
        migrations.CreateModel(
            name='ContactMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('subject', models.CharField(blank=True, max_length=200)),
                ('message', models.TextField()),
                ('is_read', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('code', models.CharField(max_length=50, unique=True)),
                ('discount_type', models.CharField(choices=[('percentage', 'Percentage'), ('fixed', 'Fixed Amount')], max_length=20)),
                ('discount_value', models.DecimalField(decimal_places=2, max_digits=8)),
                ('min_order_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('max_discount_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('usage_limit', models.PositiveIntegerField(blank=True, null=True)),
                ('used_count', models.PositiveIntegerField(default=0)),
                ('valid_from', models.DateTimeField()),
                ('valid_until', models.DateTimeField()),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Material',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Newsletter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('subscribed_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='ShippingZone',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('governorates', models.JSONField()),
                ('shipping_cost', models.DecimalField(decimal_places=2, max_digits=8)),
                ('free_shipping_threshold', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Size',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('description', models.CharField(blank=True, max_length=100)),
                ('order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ['order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Store',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('name', models.CharField(max_length=100)),
                ('address', models.TextField()),
                ('city', models.CharField(max_length=50)),
                ('phone_number', models.CharField(max_length=20)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('is_active', models.BooleanField(default=True)),
                ('opening_hours', models.CharField(blank=True, help_text='e.g., Mon-Fri: 9AM-9PM', max_length=200)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('slug', models.SlugField(unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to='categories/')),
                ('is_active', models.BooleanField(default=True)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='store.category')),
            ],
            options={
                'verbose_name_plural': 'Categories',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(max_length=200, unique=True)),
                ('description', models.TextField()),
                ('short_description', models.CharField(blank=True, max_length=300)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('sale_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('cost_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('sku', models.CharField(max_length=100, unique=True)),
                ('weight', models.DecimalField(blank=True, decimal_places=2, help_text='Weight in kg', max_digits=8, null=True)),
                ('dimensions_length', models.DecimalField(blank=True, decimal_places=2, help_text='Length in cm', max_digits=8, null=True)),
                ('dimensions_width', models.DecimalField(blank=True, decimal_places=2, help_text='Width in cm', max_digits=8, null=True)),
                ('dimensions_height', models.DecimalField(blank=True, decimal_places=2, help_text='Height in cm', max_digits=8, null=True)),
                ('stock_quantity', models.PositiveIntegerField(default=0)),
                ('low_stock_threshold', models.PositiveIntegerField(default=5)),
                ('condition', models.CharField(choices=[('new', 'New'), ('refurbished', 'Refurbished'), ('used', 'Used')], default='new', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('is_featured', models.BooleanField(default=False)),
                ('is_on_sale', models.BooleanField(default=False)),
                ('is_best_seller', models.BooleanField(default=False)),
                ('meta_title', models.CharField(blank=True, max_length=200)),
                ('meta_description', models.CharField(blank=True, max_length=300)),
                ('min_order_quantity', models.PositiveIntegerField(default=1)),
                ('max_order_quantity', models.PositiveIntegerField(blank=True, null=True)),
                ('available_colors', models.ManyToManyField(blank=True, related_name='products', to='store.color')),
                ('brand', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='store.brand')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='store.category')),
                ('materials', models.ManyToManyField(blank=True, to='store.material')),
                ('available_sizes', models.ManyToManyField(blank=True, related_name='products', to='store.size')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SavedDesign',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('design_data', models.JSONField()),
                ('thumbnail', models.ImageField(blank=True, null=True, upload_to='saved_designs/')),
                ('is_public', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_designs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('phone_number', models.CharField(blank=True, max_length=20)),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('gender', models.CharField(blank=True, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other'), ('prefer_not_to_say', 'Prefer not to say')], max_length=20)),
                ('avatar', models.ImageField(blank=True, null=True, upload_to='avatars/')),
                ('newsletter_subscribed', models.BooleanField(default=False)),
                ('preferred_store', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='store.store')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Wishlist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='store.product')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('full_name', models.CharField(max_length=100)),
                ('address_line_1', models.CharField(max_length=200)),
                ('address_line_2', models.CharField(blank=True, max_length=200)),
                ('governorate', models.CharField(max_length=50)),
                ('district', models.CharField(blank=True, max_length=50)),
                ('city', models.CharField(max_length=50)),
                ('postal_code', models.CharField(blank=True, max_length=10)),
                ('phone_number', models.CharField(blank=True, max_length=20)),
                ('address_type', models.CharField(choices=[('shipping', 'Shipping'), ('billing', 'Billing'), ('both', 'Both')], default='both', max_length=20)),
                ('is_default', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='addresses', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Addresses',
                'constraints': [models.UniqueConstraint(condition=models.Q(('is_default', True)), fields=('user', 'address_type', 'is_default'), name='unique_default_address_per_type')],
            },
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('image', models.ImageField(upload_to='products/')),
                ('alt_text', models.CharField(blank=True, max_length=200)),
                ('is_primary', models.BooleanField(default=False)),
                ('order', models.PositiveIntegerField(default=0)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='store.product')),
            ],
            options={
                'ordering': ['order', 'created_at'],
                'constraints': [models.UniqueConstraint(condition=models.Q(('is_primary', True)), fields=('product', 'is_primary'), name='unique_primary_image_per_product')],
            },
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('rating', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('title', models.CharField(blank=True, max_length=200)),
                ('comment', models.TextField()),
                ('is_verified_purchase', models.BooleanField(default=False)),
                ('is_approved', models.BooleanField(default=True)),
                ('helpful_count', models.PositiveIntegerField(default=0)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='store.product')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'unique_together': {('product', 'user')},
            },
        ),
        migrations.CreateModel(
            name='ProductVariant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sku', models.CharField(max_length=50, unique=True)),
                ('price_adjustment', models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('stock_quantity', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('color', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='store.color')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='store.product')),
                ('size', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='store.size')),
            ],
            options={
                'unique_together': {('product', 'color', 'size')},
            },
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['slug'], name='store_produ_slug_361302_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['category', 'is_active'], name='store_produ_categor_591340_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['is_featured', 'is_active'], name='store_produ_is_feat_74e391_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['sku'], name='store_produ_sku_8a55cb_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['price'], name='store_produ_price_2d55a6_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='wishlist',
            unique_together={('user', 'product')},
        ),
    ]
