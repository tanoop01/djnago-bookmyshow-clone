import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from movies.models import Movie, Theater, Seat


AUTHENTIC_MOVIES = [
    {
        'name': 'Stree 2: Sarkate Ka Aatank',
        'genre': 'comedy',
        'language': 'hindi',
        'rating': 9.2,
        'price': 250.00,
        'duration_mins': 149,
        'age_certification': 'U/A 16+',
        'cast': 'Shraddha Kapoor, Rajkummar Rao, Pankaj Tripathi, Abhishek Banerjee, Aparshakti Khurana',
        'description': 'The town of Chanderi is haunted once again, this time by a headless entity known as Sarkate. Stree returns to save the townspeople alongside Vicky and his hilarious gang.',
        'image_url': 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=600&auto=format&fit=crop',
        'trailer_url': 'https://www.youtube.com/watch?v=KVnheXwqF05'
    },
    {
        'name': 'Kalki 2898 AD',
        'genre': 'sci_fi',
        'language': 'telugu',
        'rating': 9.0,
        'price': 350.00,
        'duration_mins': 180,
        'age_certification': 'U/A 13+',
        'cast': 'Prabhas, Amitabh Bachchan, Kamal Haasan, Deepika Padukone, Disha Patani',
        'description': 'Set in a post-apocalyptic world in the year 2898 AD, a modern avatar of Vishnu descends to Earth to protect the pregnant SUM-80 from the tyrannical ruler Supreme Yaskin.',
        'image_url': 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=600&auto=format&fit=crop',
        'trailer_url': 'https://www.youtube.com/watch?v=kQDd1AhGIHw'
    },
    {
        'name': 'Deadpool & Wolverine',
        'genre': 'action',
        'language': 'english',
        'rating': 9.1,
        'price': 450.00,
        'duration_mins': 128,
        'age_certification': 'A',
        'cast': 'Ryan Reynolds, Hugh Jackman, Emma Corrin, Morena Baccarin, Rob Delaney',
        'description': 'Wolverine is recovering from his injuries when he crosses paths with the loudmouth Deadpool. They team up to defeat a common enemy threatening the multiverse.',
        'image_url': 'https://images.unsplash.com/photo-1568832359672-e36cf5d74f54?w=600&auto=format&fit=crop',
        'trailer_url': 'https://www.youtube.com/watch?v=73_1biulk6s'
    },
    {
        'name': 'Jawan',
        'genre': 'action',
        'language': 'hindi',
        'rating': 8.8,
        'price': 280.00,
        'duration_mins': 169,
        'age_certification': 'U/A 13+',
        'cast': 'Shah Rukh Khan, Nayanthara, Vijay Sethupathi, Deepika Padukone, Priyamani',
        'description': 'A high-octane action thriller highlighting the emotional journey of a man who is set to rectify the wrongs in society with a team of skilled women vigilantes.',
        'image_url': 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=600&auto=format&fit=crop',
        'trailer_url': 'https://www.youtube.com/watch?v=COv52Qyctws'
    },
    {
        'name': 'Animal',
        'genre': 'action',
        'language': 'hindi',
        'rating': 8.6,
        'price': 300.00,
        'duration_mins': 201,
        'age_certification': 'A',
        'cast': 'Ranbir Kapoor, Anil Kapoor, Bobby Deol, Rashmika Mandanna, Triptii Dimri',
        'description': 'A fiercely loyal son embarks on a violent rampage of retribution after an assassination attempt on his distant, wealthy father.',
        'image_url': 'https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=600&auto=format&fit=crop',
        'trailer_url': 'https://www.youtube.com/watch?v=DypJqucvOee'
    },
    {
        'name': 'Dune: Part Two',
        'genre': 'adventure',
        'language': 'english',
        'rating': 9.4,
        'price': 500.00,
        'duration_mins': 166,
        'age_certification': 'U/A 13+',
        'cast': 'Timothée Chalamet, Zendaya, Rebecca Ferguson, Javier Bardem, Austin Butler',
        'description': 'Paul Atreides unites with Chani and the Fremen while seeking revenge against the conspirators who destroyed his family.',
        'image_url': 'https://images.unsplash.com/photo-1534447677768-be436bb09401?w=600&auto=format&fit=crop',
        'trailer_url': 'https://www.youtube.com/watch?v=Way9Dexny3w'
    },
    {
        'name': 'Oppenheimer',
        'genre': 'biography',
        'language': 'english',
        'rating': 9.5,
        'price': 400.00,
        'duration_mins': 180,
        'age_certification': 'U/A 16+',
        'cast': 'Cillian Murphy, Emily Blunt, Matt Damon, Robert Downey Jr., Florence Pugh',
        'description': 'The story of American scientist J. Robert Oppenheimer and his role in the development of the atomic bomb during World War II.',
        'image_url': 'https://images.unsplash.com/photo-1440404653325-ab127d49abc1?w=600&auto=format&fit=crop',
        'trailer_url': 'https://www.youtube.com/watch?v=uYPbbksJxIg'
    },
    {
        'name': 'Avatar: The Way of Water',
        'genre': 'sci_fi',
        'language': 'english',
        'rating': 9.3,
        'price': 600.00,
        'duration_mins': 192,
        'age_certification': 'U/A 13+',
        'cast': 'Sam Worthington, Zoe Saldana, Sigourney Weaver, Stephen Lang, Kate Winslet',
        'description': 'Jake Sully lives with his newfound family formed on the extrasolar moon Pandora. Once a familiar threat returns, Jake must work with Neytiri and the army of the Na\'vi to protect their home.',
        'image_url': 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=600&auto=format&fit=crop',
        'trailer_url': 'https://www.youtube.com/watch?v=d9MyW72ELq0'
    },
    {
        'name': 'Pushpa 2: The Rule',
        'genre': 'action',
        'language': 'telugu',
        'rating': 9.1,
        'price': 380.00,
        'duration_mins': 175,
        'age_certification': 'U/A 16+',
        'cast': 'Allu Arjun, Rashmika Mandanna, Fahadh Faasil, Jagapathi Babu',
        'description': 'The clash continues between red sandalwood smuggler Pushpa Raj and SP Bhanwar Singh Shekhawat in this epic high-voltage action saga.',
        'image_url': 'https://images.unsplash.com/photo-1542204165-65bf26472b9b?w=600&auto=format&fit=crop',
        'trailer_url': 'https://www.youtube.com/watch?v=1kGA80iFk6w'
    },
    {
        'name': 'Inside Out 2',
        'genre': 'animation',
        'language': 'english',
        'rating': 8.9,
        'price': 220.00,
        'duration_mins': 96,
        'age_certification': 'U',
        'cast': 'Amy Poehler, Maya Hawke, Kensington Tallman, Liza Lapira, Tony Hale',
        'description': 'Disney and Pixar\'s Inside Out 2 returns to the mind of newly minted teenager Riley just as headquarters is undergoing a sudden demolition to make room for Anxiety!',
        'image_url': 'https://images.unsplash.com/photo-1534447677768-be436bb09401?w=600&auto=format&fit=crop',
        'trailer_url': 'https://www.youtube.com/watch?v=LEjhY15eCx0'
    }
]

THEATERS_DATA = [
    # Mumbai
    {'name': 'PVR ICON Phoenix Palladium', 'city': 'mumbai'},
    {'name': 'INOX Megaplex Inorbit Mall', 'city': 'mumbai'},
    {'name': 'Cinepolis Fun Republic', 'city': 'mumbai'},

    # Delhi
    {'name': 'PVR Director\'s Cut Vasant Kunj', 'city': 'delhi'},
    {'name': 'INOX Select Citywalk Saket', 'city': 'delhi'},

    # Bangalore
    {'name': 'PVR Superplex Forum Mall Koramangala', 'city': 'bangalore'},
    {'name': 'INOX Orion Mall Rajajinagar', 'city': 'bangalore'},

    # Hyderabad
    {'name': 'AMB Cinemas Gachibowli', 'city': 'hyderabad'},
    {'name': 'PVR Irrum Manzil', 'city': 'hyderabad'},

    # Jalandhar & Punjab
    {'name': 'PVR Curo High Street Jalandhar', 'city': 'jalandhar'},
    {'name': 'PVR MBD Neopolis Ludhiana', 'city': 'ludhiana'},
    {'name': 'INOX VR Punjab Mall Amritsar', 'city': 'amritsar'},
    {'name': 'PVR Elante Mall Chandigarh', 'city': 'chandigarh'},

    # Pune & Ahmedabad
    {'name': 'PVR Market City Pune', 'city': 'pune'},
    {'name': 'Cinepolis Alpha One Mall Ahmedabad', 'city': 'ahmedabad'},
]

SCREENS_AND_TIMES = [
    ('Screen 1', 9, 30),     # 09:30 AM (Morning)
    ('Screen 2', 13, 15),    # 01:15 PM (Afternoon)
    ('IMAX 3D', 16, 45),     # 04:45 PM (Afternoon/Evening)
    ('VIP Screen', 19, 30),  # 07:30 PM (Evening)
    ('Dolby Atmos', 21, 45), # 09:45 PM (Night)
]


class Command(BaseCommand):
    help = 'Seeds authentic movies, realistic varied prices, 60-seat matrix per screen, and diverse showtimes'

    def handle(self, *args, **options):
        self.stdout.write("Cleaning legacy dummy movies...")
        
        # Remove old test/dummy movies if existing
        dummy_names = ['ergeg', 'movie1', 'movie 3', 'movie4', 'avengers', 'ohh my dog', 'aryabhatt ka zero', 'khel khel mein', 'jeevan bheema yojana']
        Movie.objects.filter(name__in=dummy_names).delete()

        created_movies = []
        now = timezone.now()

        # Seed Authentic Movies
        for mdata in AUTHENTIC_MOVIES:
            movie, created = Movie.objects.update_or_create(
                name=mdata['name'],
                defaults={
                    'genre': mdata['genre'],
                    'language': mdata['language'],
                    'rating': mdata['rating'],
                    'price': mdata['price'],
                    'duration_mins': mdata['duration_mins'],
                    'age_certification': mdata['age_certification'],
                    'cast': mdata['cast'],
                    'description': mdata['description'],
                    'trailer_url': mdata['trailer_url'],
                    'release_date': now.date() - timedelta(days=random.randint(10, 60))
                }
            )
            created_movies.append(movie)

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(created_movies)} authentic movies with varied prices!"))

        # Seed Theaters & Showtimes
        created_theaters = 0
        total_seats_created = 0

        for t_info in THEATERS_DATA:
            for movie in created_movies[:4]: # Link top 4 movies per theater location
                for screen_name, hour, minute in SCREENS_AND_TIMES:
                    # Construct specific showtime date and time
                    show_datetime = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=1)
                    
                    theater, t_created = Theater.objects.get_or_create(
                        name=t_info['name'],
                        movie=movie,
                        screen=screen_name,
                        city=t_info['city'],
                        defaults={'time': show_datetime}
                    )
                    
                    # Update showtime if already exists
                    theater.time = show_datetime
                    theater.save()
                    created_theaters += 1

                    # Seed 60 Seats (Rows A to F, Seats 1 to 10)
                    rows = ['A', 'B', 'C', 'D', 'E', 'F']
                    for r in rows:
                        for n in range(1, 11):
                            s_num = f"{r}{n}"
                            seat, s_created = Seat.objects.get_or_create(
                                theater=theater,
                                seat_number=s_num
                            )
                            if s_created:
                                total_seats_created += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully configured {created_theaters} theater showtimes and {total_seats_created} seats!"))
