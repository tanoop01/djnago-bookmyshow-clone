from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from movies.models import Event

SAMPLE_EVENTS = [
    # Live Events
    {
        'name': 'Lollapalooza India 2026',
        'category': 'events',
        'city': 'mumbai',
        'venue_name': 'Mahalaxmi Race Course, Mumbai',
        'price': 2999.00,
        'rating': 4.9,
        'organizer': 'BookMySeat Live & BookMyShow',
        'duration_mins': 480,
        'language': 'English / Hindi',
        'image_url': 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=600&auto=format&fit=crop',
        'banner_url': 'https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=1200&auto=format&fit=crop',
        'description': 'Asia\'s biggest multi-genre music & culture festival returning to Mumbai with global headliners and epic stage experiences!'
    },
    {
        'name': 'Zakir Khan Live - Tathastu Special',
        'category': 'events',
        'city': 'delhi',
        'venue_name': 'Siri Fort Auditorium, New Delhi',
        'price': 999.00,
        'rating': 4.8,
        'organizer': 'OML Comedy',
        'duration_mins': 90,
        'language': 'Hindi',
        'image_url': 'https://images.unsplash.com/photo-1585699324551-f6c309eedeca?w=600&auto=format&fit=crop',
        'banner_url': 'https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=1200&auto=format&fit=crop',
        'description': 'Catch India\'s favorite Sakht Launda Zakir Khan live as he performs his newest hilarious stand-up comedy special.'
    },
    {
        'name': 'India Tech & AI Conclave 2026',
        'category': 'events',
        'city': 'bangalore',
        'venue_name': 'BIEC Expo Center, Bengaluru',
        'price': 1499.00,
        'rating': 4.7,
        'organizer': 'TechIndia Forum',
        'duration_mins': 360,
        'language': 'English',
        'image_url': 'https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=600&auto=format&fit=crop',
        'banner_url': 'https://images.unsplash.com/photo-1505373877841-8d25f7d46678?w=1200&auto=format&fit=crop',
        'description': 'The premier technology expo bringing together AI leaders, founders, and innovators for keynotes and networking.'
    },

    # Plays & Theater
    {
        'name': 'Mughal-E-Azam - The Grand Musical',
        'category': 'plays',
        'city': 'mumbai',
        'venue_name': 'NCPA Jamshed Bhabha Theatre, Mumbai',
        'price': 1250.00,
        'rating': 4.9,
        'organizer': 'Shapoorji Pallonji & NCPA',
        'duration_mins': 150,
        'language': 'Hindi / Urdu',
        'image_url': 'https://images.unsplash.com/photo-1460723237483-7a6dc9d0b212?w=600&auto=format&fit=crop',
        'banner_url': 'https://images.unsplash.com/photo-1507676184212-d03ab07a01bf?w=1200&auto=format&fit=crop',
        'description': 'Feroz Abbas Khan\'s iconic Broadway-style musical featuring live singing, Manish Malhotra costumes, and mesmerizing choreography.'
    },
    {
        'name': 'Taj Mahal Ka Tender - Political Satire',
        'category': 'plays',
        'city': 'delhi',
        'venue_name': 'Kamani Auditorium, New Delhi',
        'price': 500.00,
        'rating': 4.6,
        'organizer': 'Pierrot\'s Troupe',
        'duration_mins': 110,
        'language': 'Hindi',
        'image_url': 'https://images.unsplash.com/photo-1503095396549-807759245b35?w=600&auto=format&fit=crop',
        'banner_url': 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=1200&auto=format&fit=crop',
        'description': 'A hilarious satirical play about red tape and bureaucratic delays if Shah Jahan had tried to build the Taj Mahal today.'
    },

    # Sports Matches
    {
        'name': 'IPL T20 Final Match 2026',
        'category': 'sports',
        'city': 'ahmedabad',
        'venue_name': 'Narendra Modi Stadium, Ahmedabad',
        'price': 1500.00,
        'rating': 4.9,
        'organizer': 'BCCI',
        'duration_mins': 240,
        'language': 'English / Hindi',
        'image_url': 'https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?w=600&auto=format&fit=crop',
        'banner_url': 'https://images.unsplash.com/photo-1531415074968-036ba1b575da?w=1200&auto=format&fit=crop',
        'description': 'Experience the electric atmosphere of the grand finale of India\'s biggest T20 cricket league live in the world\'s largest stadium!'
    },
    {
        'name': 'ISL Football Derby - Mumbai City vs Mohun Bagan',
        'category': 'sports',
        'city': 'mumbai',
        'venue_name': 'Mumbai Football Arena, Andheri',
        'price': 400.00,
        'rating': 4.7,
        'organizer': 'Indian Super League',
        'duration_mins': 120,
        'language': 'English / Hindi',
        'image_url': 'https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=600&auto=format&fit=crop',
        'banner_url': 'https://images.unsplash.com/photo-1489944440615-453fc2b6a9a9?w=1200&auto=format&fit=crop',
        'description': 'High-octane Indian Super League football action as top clubs clash for supremacy in Mumbai.'
    },

    # Music & Concerts
    {
        'name': 'A.R. Rahman Live Symphony Concert',
        'category': 'music',
        'city': 'chennai',
        'venue_name': 'YMCA Grounds, Nandanam, Chennai',
        'price': 1999.00,
        'rating': 5.0,
        'organizer': 'KM Music Conservatory',
        'duration_mins': 210,
        'language': 'Tamil / Hindi / English',
        'image_url': 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=600&auto=format&fit=crop',
        'banner_url': 'https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=1200&auto=format&fit=crop',
        'description': 'An unforgettable evening with Oscar-winning maestro A.R. Rahman performing his timeless classics accompanied by a full orchestra.'
    },
    {
        'name': 'Coldplay - Music of the Spheres World Tour',
        'category': 'music',
        'city': 'mumbai',
        'venue_name': 'DY Patil Stadium, Navi Mumbai',
        'price': 3500.00,
        'rating': 4.9,
        'organizer': 'BookMyShow Live',
        'duration_mins': 180,
        'language': 'English',
        'image_url': 'https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=600&auto=format&fit=crop',
        'banner_url': 'https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=1200&auto=format&fit=crop',
        'description': 'The world-famous British rock band returns to India with light shows, confetti, and legendary anthems!'
    },
    {
        'name': 'Sunburn Goa Music Festival 2026',
        'category': 'music',
        'city': 'pune',
        'venue_name': 'Vagator Beach Arena, Goa',
        'price': 2499.00,
        'rating': 4.8,
        'organizer': 'Percept Live',
        'duration_mins': 360,
        'language': 'English',
        'image_url': 'https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=600&auto=format&fit=crop',
        'banner_url': 'https://images.unsplash.com/photo-1506157786151-b8491531f063?w=1200&auto=format&fit=crop',
        'description': 'Asia\'s premier Electronic Dance Music (EDM) festival featuring top global DJs, laser shows, and beach vibes.'
    }
]


class Command(BaseCommand):
    help = 'Seeds sample Events, Plays, Sports matches, and Music concerts'

    def handle(self, *args, **options):
        now = timezone.now()
        created_count = 0

        for i, item in enumerate(SAMPLE_EVENTS):
            event_date = now + timedelta(days=i + 3, hours=i * 2)
            event, created = Event.objects.update_or_create(
                name=item['name'],
                defaults={
                    'category': item['category'],
                    'city': item['city'],
                    'venue_name': item['venue_name'],
                    'price': item['price'],
                    'rating': item['rating'],
                    'organizer': item['organizer'],
                    'duration_mins': item['duration_mins'],
                    'language': item['language'],
                    'image_url': item['image_url'],
                    'banner_url': item['banner_url'],
                    'description': item['description'],
                    'event_date': event_date,
                }
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {len(SAMPLE_EVENTS)} events ({created_count} new)!'))
