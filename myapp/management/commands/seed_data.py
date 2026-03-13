from django.core.management.base import BaseCommand
from myapp.models import PollingStation

class Command(BaseCommand):
    help = 'Seeds initial polling station data'

    def handle(self, *args, **kwargs):
        stations = [
            { 'id': 'ps-1', 'name': 'Garissa Primary School', 'registered_voters': 2500, 'zone_type': 'stronghold' },
            { 'id': 'ps-2', 'name': 'Township Secondary', 'registered_voters': 1800, 'zone_type': 'swing' },
            { 'id': 'ps-3', 'name': 'Bulla Iftin Primary', 'registered_voters': 2200, 'zone_type': 'swing' },
            { 'id': 'ps-4', 'name': 'Garissa DEB Primary', 'registered_voters': 1500, 'zone_type': 'weak' },
            { 'id': 'ps-5', 'name': 'Bulla Punda Primary', 'registered_voters': 1900, 'zone_type': 'stronghold' },
            { 'id': 'ps-6', 'name': 'Iftin Primary School', 'registered_voters': 2100, 'zone_type': 'swing' },
            { 'id': 'ps-7', 'name': 'Garissa High School', 'registered_voters': 1700, 'zone_type': 'weak' },
            { 'id': 'ps-8', 'name': 'Township Chief\'s Camp', 'registered_voters': 1400, 'zone_type': 'stronghold' },
        ]

        for s in stations:
            PollingStation.objects.update_or_create(
                id=s['id'],
                defaults={
                    'name': s['name'],
                    'registered_voters': s['registered_voters'],
                    'zone_type': s['zone_type']
                }
            )
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded polling stations'))
