from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg, Count

# Genre Model
class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

# Person Model
class Person(models.Model):
    """ Represents an Actor, Director, or Writer """
    name = models.CharField(max_length=255)
    photo = models.ImageField(upload_to='persons/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

# Movie Model
class Movie(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    release_date = models.DateField()
    poster = models.ImageField(upload_to='movies/posters/', blank=True, null=True)
    video_file = models.FileField(upload_to='movies/videos/', blank=True, null=True)

    # Relationships
    genres = models.ManyToManyField(Genre, related_name='movies')

    # Performance / Denormalized Fields
    average_rating = models.FloatField(default=0.0, )
    total_review_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-release_date']

    def __str__(self):
        return self.title

# Movies <-> People with Roles
class MovieCrew(models.Model):
    """ 
    Intermediate table to link Person <-> Movie with a specific Role.
    This replaces the simple ManyToMany/ForeignKey on the Movie model.
    """
    ROLE_CHOICES = (
        ('director', 'Director'),
        ('actor', 'Actor'),
        ('writer', 'Writer'),
    )

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='crew')
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='movie_credits')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    
    # I added this back because it's standard for IMDb (e.g., "Iron Man")
    character_name = models.CharField(max_length=255, blank=True, null=True, help_text="Only for actors")
    
    class Meta:
        # Ensures a person can't have the EXACT same role twice in one movie 
        # (e.g., Listed as Director twice)
        unique_together = ('movie', 'person', 'role')

    def __str__(self):
        return f"{self.person.name} ({self.role}) - {self.movie.title}"


class Review(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Prevent multiple reviews per user per movie
        unique_together = ('movie', 'user') 
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.name} - {self.movie.title} ({self.rating})"

# Handlers to auto-update Movie stats on Review changes
@receiver(post_save, sender=Review)
@receiver(post_delete, sender=Review)
def update_movie_stats(sender, instance, **kwargs):
    """
    Auto-updates both average rating AND total review count
    whenever a review is added, updated, or deleted.
    """
    movie = instance.movie

    # Calculate stats
    stats = movie.reviews.aggregate(
        avg=Avg('rating'),
        count=Count('id')
    )

    # Use 0 if there are no reviews (handle NoneType)
    movie.average_rating = round(stats['avg'] or 0, 1)
    movie.total_review_count = stats['count'] or 0
    movie.save()