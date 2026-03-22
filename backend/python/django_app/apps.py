from django.apps import AppConfig


class DjangoAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_app"
    label = "django_app"

    def ready(self):
        import mongoengine
        from django.conf import settings
        from django_app.domain import product_service, product_category_service
        from django_app.repository.product_repository_mongo import MongoProductRepository
        from django_app.repository.category_repository_mongo import MongoProductCategoryRepository
        from django_app.repository.product_document import ProductDocument
        from django_app.repository.category_document import ProductCategoryDocument

        mongoengine.connect(
            db=settings.MONGO_DB,
            host=settings.MONGO_HOST,
            port=settings.MONGO_PORT,
            username=settings.MONGO_USER,
            password=settings.MONGO_PASS,
            authentication_source=settings.MONGO_AUTH_SOURCE,
        )
        product_service.set_repository(MongoProductRepository())
        product_category_service.set_repository(MongoProductCategoryRepository())

        if ProductCategoryDocument.objects.count() == 0:
            ProductCategoryDocument(title="Food", description="Food and groceries").save()
            ProductCategoryDocument(title="Kitchen Essentials", description="Kitchen supplies").save()
            ProductCategoryDocument(title="Electronics", description="Electronic devices").save()

        from mongoengine.queryset.visitor import Q
        needs_migration = ProductDocument.objects(Q(category_id=None) | Q(category_id__exists=False)).count() > 0
        if needs_migration:
            uncat = ProductCategoryDocument.objects(title="Uncategorized").first()
            if not uncat:
                uncat = ProductCategoryDocument(title="Uncategorized", description="Products without category")
                uncat.save()
            for doc in ProductDocument.objects(Q(category_id=None) | Q(category_id__exists=False)):
                doc.category_id = uncat.id
                doc.save()
