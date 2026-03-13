from myapp.models import PollingStation, Voter

approved_names = ['Library', 'Garissa Ndogo', 'Chief Camp', 'NEP Girls']

# 1. Ensure approved stations exist
approved_stations = {}
for name in approved_names:
    ps, created = PollingStation.objects.get_or_create(name=name, defaults={'zone_type': 'swing'})
    approved_stations[name] = ps
    if created:
        print(f"Created station: {name}")

# 2. Reassign voters from non-approved stations and delete them
default_ps = approved_stations['Library']
for ps in PollingStation.objects.all():
    if ps.name not in approved_names:
        voter_count = ps.voters.count()
        if voter_count > 0:
            print(f"Reassigning {voter_count} voters from {ps.name} to Library")
            ps.voters.update(polling_station=default_ps)
        print(f"Deleting non-approved station: {ps.name}")
        ps.delete()

print("Database sync complete.")
