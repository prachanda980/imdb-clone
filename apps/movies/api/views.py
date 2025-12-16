from rest_framework import viewsets, filters, permissions, status
from rest_framework.response import Response
from django.core.cache import cache
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError
from .permissions import IsAdminOrReadOnly, IsOwnerOrReadOnly
from apps.movies.models import Movie, Genre, Person, Review, MovieCrew
from .serializers import (
    MovieSerializer,
    GenreSerializer,
    PersonSerializer,
    ReviewSerializer,
    MovieCrewWriteSerializer,
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAdminOrReadOnly]


class PersonViewSet(viewsets.ModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["name"]
    filter_backends = [filters.SearchFilter]


class MovieViewSet(viewsets.ModelViewSet):
    """
    Main Movie Endpoint.
    Supports: Filtering, Searching, Ordering, and Caching.
    """

    queryset = Movie.objects.prefetch_related("genres", "crew__person", "reviews")
    serializer_class = MovieSerializer
    permission_classes = [IsAdminOrReadOnly]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["genres__name", "release_date"]
    search_fields = ["title", "description", "crew__person__name"]
    ordering_fields = ["average_rating", "release_date", "total_review_count"]

    # LIST (CACHE) 
    def list(self, request, *args, **kwargs):
        # If query params exist → skip cache
        if request.query_params:
            return super().list(request, *args, **kwargs)

        cache_key = "movies:list"
        cached_data = cache.get(cache_key)

        if cached_data:
            return Response(cached_data)

        response = super().list(request, *args, **kwargs)

        cache.set(cache_key, response.data, timeout=settings.CACHE_TTL)
        return response

    #  RETRIEVE (CACHE)
    def retrieve(self, request, *args, **kwargs):
        movie_id = kwargs["pk"]
        cache_key = f"movies:detail:{movie_id}"

        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        response = super().retrieve(request, *args, **kwargs)

        cache.set(cache_key, response.data, timeout=settings.CACHE_TTL)
        return response

    # CACHE INVALIDATION
    def perform_create(self, serializer):
        serializer.save()
        cache.delete("movies:list")

    def perform_update(self, serializer):
        movie = serializer.save()
        cache.delete("movies:list")
        cache.delete(f"movies:detail:{movie.id}")

    def perform_destroy(self, instance):
        movie_id = instance.id
        instance.delete()
        cache.delete("movies:list")
        cache.delete(f"movies:detail:{movie_id}")


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        """
        Only return reviews for the specific movie in the URL.
        URL: /api/v1/movies/{movie_pk}/reviews/
        """
        return Review.objects.filter(movie_id=self.kwargs["movie_pk"])

    def perform_create(self, serializer):
        """
        Automatically assign the logged-in User and the Movie ID.
        """
        movie_id = self.kwargs["movie_pk"]
        movie = Movie.objects.get(pk=movie_id)

        # Check for duplicate review
        if Review.objects.filter(movie=movie, user=self.request.user).exists():
            raise ValidationError("You have already reviewed this movie.")

        serializer.save(user=self.request.user, movie=movie)


class MovieCrewViewSet(viewsets.ModelViewSet):
    """
    Dedicated endpoint to manage the cast of a movie.
    URL: /api/v1/movies/{movie_pk}/crew/
    """

    serializer_class = MovieCrewWriteSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        return MovieCrew.objects.filter(movie_id=self.kwargs["movie_pk"])

    def perform_create(self, serializer):
        movie_id = self.kwargs["movie_pk"]
        serializer.save(movie_id=movie_id)
