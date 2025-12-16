import os
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from apps.movies.models import Movie, Genre, Person, MovieCrew, Review


# Custom Validators


def validate_file_size(file_field):
    """
    Validator to ensure file size is under 20MB.
    """
    LIMIT_MB = 20
    if file_field.size > LIMIT_MB * 1024 * 1024:
        raise ValidationError(f"File too large. Size should not exceed {LIMIT_MB} MB.")


def validate_image_extension(file_field):
    """
    Validator to ensure file is a valid image type.
    """
    ext = os.path.splitext(file_field.name)[1]
    valid_extensions = [".jpg", ".jpeg", ".png", ".webp"]
    if not ext.lower() in valid_extensions:
        raise ValidationError(
            "Unsupported file extension. Allowed: .jpg, .jpeg, .png, .webp"
        )


# Helper Serializers
class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["id", "name"]


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ["id", "name", "photo", "bio"]


# Nested Serializers
class MovieCrewSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="person.id")
    name = serializers.ReadOnlyField(source="person.name")
    photo = serializers.ImageField(source="person.photo", read_only=True)

    class Meta:
        model = MovieCrew
        fields = ["id", "name", "photo", "role", "character_name"]


# Review Serializer
class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source="user.name")

    class Meta:
        model = Review
        fields = ["id", "user", "rating", "comment", "created_at"]


# Movie Serializer
class MovieSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    crew = MovieCrewSerializer(many=True, read_only=True)
    latest_reviews = serializers.SerializerMethodField()

    genre_ids = serializers.PrimaryKeyRelatedField(
        queryset=Genre.objects.all(), source="genres", write_only=True, many=True
    )

    class Meta:
        model = Movie
        fields = [
            "id",
            "title",
            "description",
            "release_date",
            "poster",
            "video_file",
            "average_rating",
            "total_review_count",
            "genres",
            "genre_ids",
            "crew",
            "latest_reviews",
        ]

    def get_latest_reviews(self, obj):
        reviews = obj.reviews.all()[:3]
        return ReviewSerializer(reviews, many=True).data

    # CUSTOM VALIDATIONS 

    def validate_poster(self, value):
        """Check poster size and type"""
        if value:
            validate_file_size(value)
            validate_image_extension(value)
        return value

    def validate_video_file(self, value):
        """
        Check video size (Maybe allow larger for video, e.g., 50MB)
        but strictly check extension
        """
        if value:
            # For video, 2MB is very small, but if that's the strict rule:
            validate_file_size(value)

            ext = os.path.splitext(value.name)[1]
            if not ext.lower() in [".mp4", ".mov", ".avi"]:
                raise ValidationError(
                    "Unsupported video format. Allowed: .mp4, .mov, .avi"
                )
        return value

    def validate_genre_ids(self, value):
        """Ensure at least one genre is selected"""
        if len(value) == 0:
            raise ValidationError("A movie must belong to at least one genre.")
        return value


# Crew Write Serializer
class MovieCrewWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieCrew
        fields = ["movie", "person", "role", "character_name"]
