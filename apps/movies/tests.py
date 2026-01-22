from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from apps.movies.models import Movie, Genre, Person, MovieCrew, Review
from django.core.cache import cache

User = get_user_model()

class MovieAppTests(APITestCase):
    def setUp(self):
        # Create Users
        self.admin = User.objects.create_superuser(email='admin@example.com', name='Admin User', password='password123')
        self.user = User.objects.create_user(email='testuser@example.com', name='Test User', password='password123')
        self.user2 = User.objects.create_user(email='testuser2@example.com', name='Test User 2', password='password123')

        # Create Initial Data
        self.genre = Genre.objects.create(name="Action")
        self.genre2 = Genre.objects.create(name="Drama")
        
        self.person = Person.objects.create(name="Christopher Nolan", bio="Great Director")
        self.person2 = Person.objects.create(name="Cillian Murphy", bio="Actor")

        self.movie = Movie.objects.create(
            title="Inception",
            description="A thief who steals corporate secrets...",
            release_date="2010-07-16"
        )
        self.movie.genres.add(self.genre)

        cache.clear()

    # --- GENRE TESTS ---
    def test_get_genres(self):
        # Admin can view
        self.client.force_authenticate(user=self.admin)
        url = reverse('genre-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_create_genre_admin(self):
        # Admin can create
        self.client.force_authenticate(user=self.admin)
        url = reverse('genre-list')
        data = {"name": "Sci-Fi"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Genre.objects.count(), 3)

    def test_create_genre_user_forbidden(self):
        # Regular user cannot create
        self.client.force_authenticate(user=self.user)
        url = reverse('genre-list')
        data = {"name": "Comedy"}
        response = self.client.post(url, data)
        # Assuming IsAdminOrReadOnly
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- PERSON TESTS ---
    def test_create_person(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('person-list')
        data = {"name": "Leonardo DiCaprio", "bio": "Actor"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # --- MOVIE TESTS ---
    def test_get_movies(self):
        url = reverse('movie-list')
        # Public access
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should see Inception
        data = response.data['results'] if 'results' in response.data else response.data
        self.assertEqual(len(data), 1)

    def test_create_movie(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('movie-list')
        data = {
            "title": "Interstellar",
            "description": "Space exploration",
            "release_date": "2014-11-07",
            "genre_ids": [self.genre.id, self.genre2.id]
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Movie.objects.count(), 2)
        movie = Movie.objects.get(title="Interstellar")
        self.assertEqual(movie.genres.count(), 2)

    def test_create_movie_no_genre(self):
        # Validation Check
        self.client.force_authenticate(user=self.admin)
        url = reverse('movie-list')
        data = {
            "title": "Bad Movie",
            "description": "No genre",
            "release_date": "2020-01-01",
            "genre_ids": []
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Expecting error on genre_ids
        self.assertIn("genre_ids", response.data)

    # --- CREW TESTS ---
    def test_add_crew_to_movie(self):
        self.client.force_authenticate(user=self.admin)
        # URL for movie-crew list: /api/v1/movies/{pk}/crew/
        url = reverse('movie-crew-list', args=[self.movie.id])
        data = {
            "movie": self.movie.id,
            "person": self.person.id, # Christopher Nolan
            "role": "director"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MovieCrew.objects.count(), 1)
        
        # Verify duplicated role constraint (unique_together)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- REVIEW TESTS ---
    def test_create_review(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('movie-reviews-list', args=[self.movie.id])
        data = {"rating": 9, "comment": "Amazing!"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check Stats Update
        self.movie.refresh_from_db()
        self.assertEqual(self.movie.total_review_count, 1)
        self.assertEqual(self.movie.average_rating, 9.0)

    def test_duplicate_review(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('movie-reviews-list', args=[self.movie.id])
        # DB level unique_together and ViewSet validation
        
        # 1st review
        self.client.post(url, {"rating": 8, "comment": "Cool"})
        
        # 2nd review (same user, same movie)
        response = self.client.post(url, {"rating": 10, "comment": "Again"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_average_rating_calculation(self):
        # User 1 rates 10
        self.client.force_authenticate(user=self.user)
        url = reverse('movie-reviews-list', args=[self.movie.id])
        self.client.post(url, {"rating": 10})
        
        # User 2 rates 5
        self.client.force_authenticate(user=self.user2)
        url = reverse('movie-reviews-list', args=[self.movie.id])
        self.client.post(url, {"rating": 5})

        self.movie.refresh_from_db()
        self.assertEqual(self.movie.total_review_count, 2)
        # Average (10+5)/2 = 7.5
        self.assertEqual(self.movie.average_rating, 7.5)
