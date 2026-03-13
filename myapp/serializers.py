from rest_framework import serializers
from .models import PollingStation, Voter, Message

class PollingStationSerializer(serializers.ModelSerializer):
    zoneType = serializers.CharField(source='zone_type')
    registeredVoters = serializers.IntegerField(source='registered_voters')

    class Meta:
        model = PollingStation
        fields = ['id', 'name', 'registeredVoters', 'zoneType']

class VoterSerializer(serializers.ModelSerializer):
    pollingStationId = serializers.PrimaryKeyRelatedField(
        queryset=PollingStation.objects.all(), 
        source='polling_station'
    )
    pollingStationName = serializers.SerializerMethodField()
    idNumber = serializers.CharField(source='id_number')
    phoneNumber = serializers.CharField(source='phone_number', required=False, allow_null=True)
    dob = serializers.IntegerField(required=False, allow_null=True)
    rG = serializers.BooleanField(source='r_g', required=False)
    ageGroup = serializers.CharField(source='age_group')
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
            'ageGroup', 'footballClub', 'tribe', 'ward', 'pollingCenter',
            'stream', 'mobilizedBy',
            'status', 'notes', 'optedIn',
            'createdAt', 'updatedAt'
        ]
    
    optedIn = serializers.BooleanField(source='opted_in', required=False)
    
    supportProbability = serializers.ReadOnlyField(source='support_probability')

    def get_pollingStationName(self, obj):
        return obj.polling_station.name

class MessageSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Message
        fields = [
            'id', 'voter', 'channel', 'content', 
            'direction', 'status', 'external_id', 'created_at'
        ]
