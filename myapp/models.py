from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('aspirant', 'MCA Aspirant'),
        ('staff', 'Staff'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')

    def __str__(self):
        return f"{self.username} ({self.role})"

class PollingStation(models.Model):
    id = models.CharField(primary_key=True, max_length=100, default=uuid.uuid4, editable=False) # Keep consistent with frontend strings if needed, or just use UUID
    name = models.CharField(max_length=255)
    registered_voters = models.IntegerField(default=0)
    
    ZONE_CHOICES = [
        ('stronghold', 'Stronghold'),
        ('swing', 'Swing'),
        ('weak', 'Weak'),
    ]
    zone_type = models.CharField(max_length=20, choices=ZONE_CHOICES)

    def __str__(self):
        return self.name

class Voter(models.Model):
    id = models.CharField(primary_key=True, max_length=100, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    id_number = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    
    CLAN_CHOICES = [
        ('Ogaden', 'Ogaden'),
        ('Abdalla', 'Abdalla'),
        ('Aulihan', 'Aulihan'),
        ('Abdwak', 'Abdwak'),
        ('Fai', 'Fai'),
        ('Other', 'Other'),
    ]
    clan = models.CharField(max_length=50, blank=True, null=True)
    
    polling_station = models.ForeignKey(PollingStation, on_delete=models.CASCADE, related_name='voters')
    location = models.CharField(max_length=255, blank=True, null=True)
    
    dob = models.IntegerField(blank=True, null=True, help_text="Year of Birth")
    r_g = models.BooleanField(default=False, verbose_name="Registered")

    football_club = models.CharField(max_length=100, blank=True, null=True)

    # Additional demographic fields
    tribe = models.CharField(max_length=100, blank=True, null=True)
    ward = models.CharField(max_length=100, blank=True, null=True)
    polling_center = models.CharField(max_length=255, blank=True, null=True)
    stream = models.CharField(max_length=100, blank=True, null=True)
    mobilized_by = models.CharField(max_length=255, blank=True, null=True)
    
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('likely', 'Likely'),
        ('undecided', 'Undecided'),
        ('unlikely', 'Unlikely'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='undecided')
    notes = models.TextField(blank=True, null=True)
    opted_in = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def support_probability(self):
        """
        Calculates the probability of support based on ward and registration:

        - Ward is "Township" (case-insensitive):
            - Registered (r_g=True): 90%
            - Not registered (r_g=False): 70%
        - Ward has some value other than "Township":
            - Registered: 60%
            - Not registered (NR): 80%
        - Ward is blank / missing:
            - Registered: 60%
            - Not registered (NR): 50%
        """
        ward_name = (self.ward or '').strip().lower()
        is_township = ward_name == 'township'
        has_ward = bool(ward_name)
        is_registered = bool(self.r_g)

        if is_township:
            return 90 if is_registered else 70
        if not is_registered:
            # NR outside Township
            if not has_ward:
                # NR with blank ward
                return 50
            # NR with some ward value (including "NR")
            return 80
        # Registered outside Township (any non-blank ward or blank)
        return 60

    def __str__(self):
        return self.name

class Message(models.Model):
    CHANNEL_CHOICES = [
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
    ]
    DIRECTION_CHOICES = [
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound'),
    ]
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('read', 'Read'),
    ]

    voter = models.ForeignKey(Voter, on_delete=models.CASCADE, related_name='messages')
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    content = models.TextField()
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    external_id = models.CharField(max_length=255, blank=True, null=True, help_text="ID from SMS/WhatsApp provider")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.channel} {self.direction} to {self.voter.name} at {self.created_at}"
