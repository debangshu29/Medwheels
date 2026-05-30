from django.core.management.base import BaseCommand
from django.conf import settings
import requests
import time
from map.models import Hospital

class Command(BaseCommand):
    help = 'Fetches nearby hospitals from Google Places API and saves them to the database.'

    def add_arguments(self, parser):
        parser.add_argument('--location', type=str, help='Coordinates (e.g. 22.5744,88.3629)', required=True)
        parser.add_argument('--radius', type=int, default=5000, help='Search radius in meters')

    def handle(self, *args, **kwargs):
        location = kwargs['location']
        radius = kwargs['radius']
        
        # Pull API key from Django settings securely
        api_key = settings.GOOGLE_MAPS_API_KEY
        
        if not api_key:
            self.stderr.write(self.style.ERROR("GOOGLE_MAPS_API_KEY is not set in settings."))
            return

        self.stdout.write(self.style.SUCCESS(f'Fetching hospitals near {location} within {radius}m...'))
        
        base_url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
        next_page_token = ''
        
        count = 0
        while True:
            url = f"{base_url}?location={location}&radius={radius}&type=hospital&key={api_key}"
            if next_page_token:
                url = f"{base_url}?pagetoken={next_page_token}&key={api_key}"
                
            response = requests.get(url)
            data = response.json()
            
            if response.status_code != 200 or 'results' not in data:
                self.stderr.write(self.style.ERROR(f"Error fetching data: {data.get('error_message', 'Unknown error')}"))
                break
                
            for place in data['results']:
                # Fetch detailed info (phone number, website)
                place_id = place['place_id']
                detail_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&key={api_key}"
                
                try:
                    detail_res = requests.get(detail_url).json()
                    detail_result = detail_res.get('result', {})
                    phone = detail_result.get('formatted_phone_number', '')
                    website = detail_result.get('website', '')
                except Exception as e:
                    self.stderr.write(self.style.WARNING(f"Failed to fetch details for {place.get('name')}: {e}"))
                    phone = ''
                    website = ''
                
                # Save directly to the Database instead of CSV/Excel
                Hospital.objects.update_or_create(
                    name=place['name'],
                    defaults={
                        'address': place.get('vicinity', ''),
                        'latitude': place['geometry']['location']['lat'],
                        'longitude': place['geometry']['location']['lng'],
                        'rating': place.get('rating', 0.0),
                        'phone_number': phone,
                        'website': website
                    }
                )
                count += 1
            
            next_page_token = data.get('next_page_token')
            if not next_page_token:
                break
            
            self.stdout.write(self.style.WARNING('Waiting 2 seconds for the next page token to become active...'))
            time.sleep(2)
            
        self.stdout.write(self.style.SUCCESS(f'Successfully fetched and stored {count} hospitals to the database.'))
