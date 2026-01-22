from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
import random
from apps.movies.models import Movie, Genre, Person, MovieCrew

class Command(BaseCommand):
    help = 'Populates the database with 1000 dummy movies'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting database population...")
        fake = Faker()

        # 1. Create Genres (if not enough)
        genres_list = ['Action', 'Comedy', 'Drama', 'Sci-Fi', 'Horror', 'Romance', 'Documentary', 'Thriller', 'Animation', 'Fantasy']
        db_genres = []
        for g_name in genres_list:
            genre, created = Genre.objects.get_or_create(name=g_name)
            db_genres.append(genre)
        self.stdout.write(f"- Ensure {len(db_genres)} genres exist.")

        # 2. Create Persons (Actors/Directors)
        people = []
        for _ in range(100): # Pool of 100 people
            person = Person.objects.create(
                name=fake.name(),
                bio=fake.text(max_nb_chars=200)
            )
            people.append(person)
        self.stdout.write(f"- Created 100 dummy people.")

        # 3. Create 1000 Movies
        movies_to_create = []
        # Bulk create is faster but ManyToMany relations need separate handling.
        # For simplicity and relations, robust loop is safer for M2M/ForeignKeys in this context.
        # But for 1000, loop is acceptable.
        
        for i in range(1000):
            movie = Movie.objects.create(
                title=fake.sentence(nb_words=4).replace(".", ""),
                description=fake.paragraph(nb_sentences=5),
                release_date=fake.date_between(start_date='-20y', end_date='today'),
                average_rating=round(random.uniform(1.0, 10.0), 1),
                total_review_count=random.randint(0, 500)
            )
            
            # Add Genres
            k = random.randint(1, 3)
            movie.genres.add(*random.sample(db_genres, k))
            
            # Add Crew (Director, Writer, Actor)
            director = random.choice(people)
            MovieCrew.objects.create(movie=movie, person=director, role='director')
            
            # Add 2-5 Actors
            actors = random.sample(people, random.randint(2, 5))
            for actor in actors:
                 MovieCrew.objects.create(
                     movie=movie, 
                     person=actor, 
                     role='actor', 
                     character_name=fake.first_name()
                 )

            if i % 100 == 0:
                self.stdout.write(f"  Created {i} movies...")

        self.stdout.write(self.style.SUCCESS('Successfully created 1000 dummy movies!'))
