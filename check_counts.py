import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'strategy.settings')
django.setup()

from myapp.models import Voter, PollingStation

voter_count = Voter.objects.count()
station_count = PollingStation.objects.count()

print(f"Voters: {voter_count}")
print(f"Stations: {station_count}")
