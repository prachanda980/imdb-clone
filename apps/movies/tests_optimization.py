from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from apps.movies.models import Movie, Genre, Person

User = get_user_model()

class optimizationTests(APITestCase):
    def setUp(self):
        # Create User
        self.user = User.objects.create_user(email='testuser@example.com', name='Test User', password='password123')
        self.admin = User.objects.create_superuser(email='admin@example.com', name='Admin User', password='password123')
        
        # Create Data
        self.genre = Genre.objects.create(name="Action")
        self.person = Person.objects.create(name="John Doe")
        self.movie = Movie.objects.create(
            title="Test Movie",
            description="Test Description",
            release_date="2023-01-01"
        )
        self.movie.genres.add(self.genre)

        # Clear cache before tests
        cache.clear()

    def test_genre_caching(self):
        """
        Test that Genre list endpoint is cached.
        """
        url = reverse('genre-list') # Assuming router basename 'genre'
        
        self.client.force_authenticate(user=self.admin)
        
        # First request should hit the DB
        with self.assertNumQueries(1): # 1 query to fetch genres
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Second request should come from cache (0 DB queries)
        with self.assertNumQueries(0):
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_person_caching(self):
        """
        Test that Person list endpoint is cached.
        """
        url = reverse('person-list')
        
        self.client.force_authenticate(user=self.admin)
        
        # First request DB
        with self.assertNumQueries(1): # 1 query for persons
             response = self.client.get(url)
             self.assertEqual(response.status_code, status.HTTP_200_OK)
             
        # Second request Cache
        with self.assertNumQueries(0):
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_review_throttling(self):
        """
        Test that Review creation is throttled (10/min).
        """
        # url = reverse('movie-reviews-list', kwargs={'movie_pk': self.movie.id})
        # Nested router naming convention might be slightly different depending on implementation.
        # Based on urls.py: basename="movie-reviews"
        url = reverse('movie-reviews-list', args=[self.movie.id])
        
        self.client.force_authenticate(user=self.user)

        # Create 10 reviews (Limit)
        # Note: We need to create distinct reviews or handle unique constraints if any.
        # Review model likely has unique_together(movie, user), so we might fail validation before throttling if we duplicate.
        # However, the ViewSet `perform_create` checks for duplicates manually: "You have already reviewed this movie."
        # So we can't create 10 valid reviews with the SAME user for the SAME movie easily without deleting them.
        # BUT throttling usually counts ATTEMPTS. Even 400 Bad Request counts towards throttle if configured (default is True).
        # Let's verify if failing validation counts. If not, we need multiple users or multiple movies.
        # Standard DRF throttling counts valid requests. Let's assume validation failure counts for SimpleRateThrottle? 
        # Actually AnonRateThrottle/UserRateThrottle counts all requests. ScopedRateThrottle too.
        
        for i in range(10):
            response = self.client.post(url, {'rating': 5, 'text': 'Good'}, format='json')
            # First one might be 201, subsequent 400 (duplicate), but they all count towards throttle.
            if i == 0:
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            else:
                 # Expect 400 because "You have already reviewed this movie" or Throttle
                 # Since throttle is 10/min, 10 requests pass.
                 pass

        # The 11th request should be throttled
        response = self.client.post(url, {'rating': 5, 'text': 'Good'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
