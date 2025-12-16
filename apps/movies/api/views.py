from rest_framework import viewsets, filters, permissions, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError
from .permissions import IsAdminOrReadOnly, IsOwnerOrReadOnly
from apps.movies.models import Movie, Genre, Person, Review, MovieCrew
from .serializers import (
    MovieSerializer, GenreSerializer, PersonSerializer, 
    ReviewSerializer, MovieCrewWriteSerializer
)

class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAdminOrReadOnly]

class PersonViewSet(viewsets.ModelViewSet):
    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ['name']
    filter_backends = [filters.SearchFilter]

class MovieViewSet(viewsets.ModelViewSet):
    """
    Main Movie Endpoint.
    Supports: Filtering by Genre, Searching by Title, Ordering by Rating.
    """
    # Optimized Query: Fetches Genres, Crew, and Persons in one go
    queryset = Movie.objects.prefetch_related('genres', 'crew__person', 'reviews').all()
    serializer_class = MovieSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    # Enable robust searching and filtering
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['genres__name', 'release_date'] # ?genres__name=Action
    search_fields = ['title', 'description', 'crew__person__name'] # ?search=Nolan
    ordering_fields = ['average_rating', 'release_date', 'total_review_count'] # ?ordering=-average_rating

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        """
        Only return reviews for the specific movie in the URL.
        URL: /api/v1/movies/{movie_pk}/reviews/
        """
        return Review.objects.filter(movie_id=self.kwargs['movie_pk'])

    def perform_create(self, serializer):
        """
        Automatically assign the logged-in User and the Movie ID.
        """
        movie_id = self.kwargs['movie_pk']
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
        return MovieCrew.objects.filter(movie_id=self.kwargs['movie_pk'])

    def perform_create(self, serializer):
        movie_id = self.kwargs['movie_pk']
        serializer.save(movie_id=movie_id)