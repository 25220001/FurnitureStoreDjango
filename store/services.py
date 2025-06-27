import numpy as np
import os
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.applications.resnet50 import preprocess_input
from tensorflow.keras.preprocessing import image
from sklearn.metrics.pairwise import cosine_similarity
from django.conf import settings
from django.core.cache import cache
from .models import Product, ProductImage


class ImageSimilarityService:
    def __init__(self):
        self.model = ResNet50(weights='imagenet',
                              include_top=False, pooling='avg')
        self.features_cache_key = 'product_image_features'

    def extract_features(self, img_path):
        """Extract features from image using ResNet50"""
        try:
            img = image.load_img(img_path, target_size=(224, 224))
            img_array = image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = preprocess_input(img_array)
            features = self.model.predict(img_array)
            return features.flatten()
        except Exception as e:
            return None

    def get_product_features(self, force_refresh=False):
        """Get or compute features for all product images"""
        if not force_refresh:
            cached_features = cache.get(self.features_cache_key)
            if cached_features:
                return cached_features

        # Get all active products with primary images
        products_with_images = Product.objects.filter(
            is_active=True,
            images__is_primary=True
        ).select_related().prefetch_related('images')

        product_features = {}

        for product in products_with_images:
            primary_image = product.images.filter(is_primary=True).first()
            if primary_image and primary_image.image:
                try:
                    # Get full path to image
                    image_path = os.path.join(
                        settings.MEDIA_ROOT, primary_image.image.name)

                    if os.path.exists(image_path):
                        features = self.extract_features(image_path)
                        if features is not None:
                            product_features[product.id] = {
                                'features': features.tolist(),  # Convert to list for JSON serialization
                                'product': product
                            }
                except Exception as e:
                    continue

        # Cache the features for 1 hour
        cache.set(self.features_cache_key, product_features, 3600)
        return product_features

    def find_similar_products(self, query_image_path, top_k=5):
        """Find most similar products to query image"""
        try:
            # Extract features from query image
            query_features = self.extract_features(query_image_path)
            if query_features is None:
                return []

            # Get product features from database
            product_features = self.get_product_features()

            if not product_features:
                return []

            similarities = []

            for product_id, data in product_features.items():
                try:
                    db_features = np.array(data['features'])
                    similarity = cosine_similarity(
                        [query_features], [db_features])[0][0]
                    similarities.append({
                        'product': data['product'],
                        'similarity': float(similarity),
                        'product_id': product_id
                    })
                except Exception as e:
                    continue

            # Sort by similarity (descending) and return top_k
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            return similarities[:top_k]

        except Exception as e:
            return []
