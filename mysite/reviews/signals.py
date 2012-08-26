from django.dispatch import Signal

review_uploaded = Signal(providing_args=["user", "review_request"])
