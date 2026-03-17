from rest_framework import serializers
from .models import PollingStation, Voter, Message

class PollingStationSerializer(serializers.ModelSerializer):
    zoneType = serializers.CharField(source='zone_type')
    registeredVoters = serializers.IntegerField(source='registered_voters')

    class Meta:
        model = PollingStation
        fields = ['id', 'name', 'registeredVoters', 'zoneType']

class VoterSerializer(serializers.ModelSerializer):
    clan = serializers.CharField(max_length=50, required=False, allow_null=True, allow_blank=True)
    location = serializers.CharField(max_length=255, required=False, allow_null=True, allow_blank=True)
    pollingStationId = serializers.PrimaryKeyRelatedField(
        queryset=PollingStation.objects.all(), 
        source='polling_station'
    )
    pollingStationName = serializers.ReadOnlyField(source='polling_station.name')
    idNumber = serializers.CharField(source='id_number')
    phoneNumber = serializers.CharField(source='phone_number', required=False, allow_null=True)
    dob = serializers.IntegerField(required=False, allow_null=True)
    rG = serializers.BooleanField(source='r_g', required=False)
    footballClub = serializers.CharField(source='football_club', required=False, allow_null=True)
    tribe = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    ward = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    pollingCenter = serializers.CharField(source='polling_center', required=False, allow_null=True, allow_blank=True)
    stream = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    mobilizedBy = serializers.CharField(source='mobilized_by', required=False, allow_null=True, allow_blank=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)

    class Meta:
        model = Voter
        fields = [
            'id', 'name', 'idNumber', 'phoneNumber', 'clan', 
            'pollingStationId', 'pollingStationName', 'location', 
            'dob', 'rG', 'supportProbability',
            'footballClub', 'tribe', 'ward', 'pollingCenter',
            'stream', 'mobilizedBy',
            'status', 'notes', 'optedIn',
            'createdAt', 'updatedAt'
        ]
    
    optedIn = serializers.BooleanField(source='opted_in', required=False)
    
    supportProbability = serializers.ReadOnlyField(source='support_probability')

    def validate_idNumber(self, value):
        """
        Check that the ID number is unique.
        """
        # Get the ID of the voter being updated (if any)
        voter_id = self.instance.id if self.instance else None
        
        # Look for other voters with the same ID number
        queryset = Voter.objects.filter(id_number=value)
        if voter_id:
            queryset = queryset.exclude(id=voter_id)
            
        if queryset.exists():
            raise serializers.ValidationError("A voter with this ID number already exists in the system.")
        return value


class MessageSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Message
        fields = [
            'id', 'voter', 'channel', 'content', 
            'direction', 'status', 'external_id', 'created_at'
        ]
