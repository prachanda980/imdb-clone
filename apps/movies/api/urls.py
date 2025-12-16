from django.urls import path, include
from rest_framework_nested import routers
from .views import (
    MovieViewSet,
    GenreViewSet,
    PersonViewSet,
    ReviewViewSet,
    MovieCrewViewSet,
)

# Main Router (Top Level)
router = routers.DefaultRouter()
router.register(r"movies", MovieViewSet)
router.register(r"genres", GenreViewSet)
router.register(r"persons", PersonViewSet)

# URL: /api/v1/movies/{movie_pk}/reviews/
movies_router = routers.NestedSimpleRouter(router, r"movies", lookup="movie")
movies_router.register(r"reviews", ReviewViewSet, basename="movie-reviews")

# URL: /api/v1/movies/{movie_pk}/crew/
movies_router.register(r"crew", MovieCrewViewSet, basename="movie-crew")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(movies_router.urls)),
]
