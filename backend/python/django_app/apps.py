from django.apps import AppConfig


class DjangoAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_app"
    label = "django_app"

    def ready(self):
        import mongoengine
        from django.conf import settings
        from django_app.domain import product_service
        from django_app.repository.product_repository_mongo import MongoProductRepository

        mongoengine.connect(
            db=settings.MONGO_DB,
            host=settings.MONGO_HOST,
            port=settings.MONGO_PORT,
            username=settings.MONGO_USER,
            password=settings.MONGO_PASS,
            authentication_source=settings.MONGO_AUTH_SOURCE,
        )
        product_service.set_repository(MongoProductRepository())
