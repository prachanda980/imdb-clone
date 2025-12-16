from django.contrib import admin
from .models import Genre, Person, Movie, MovieCrew, Review

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'release_date', 'average_rating', 'num_reviews')
    search_fields = ('title',)
    readonly_fields = ('average_rating', 'total_review_count')
    list_filter = ('release_date', 'genres')
    def num_reviews(self, obj):
        return obj.reviews.count()
    num_reviews.short_description = 'Number of Reviews'
@admin.register(MovieCrew)
class MovieCrewAdmin(admin.ModelAdmin):
    list_display = ('movie', 'person', 'role')
    search_fields = ('movie__title', 'person__name', 'role')
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):    
    list_display = ('movie', 'user', 'rating', 'created_at')
    search_fields = ('movie__title', 'user__email')
    list_filter = ('rating', 'created_at')