from rest_framework import viewsets, views, status, response
from rest_framework.decorators import action
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import PollingStation, Voter, Message
from .serializers import PollingStationSerializer, VoterSerializer, MessageSerializer
from .permissions import RoleBasedPermission
from .sms_service import SMSService
from .whatsapp_service import WhatsAppService
from .bulk_import import import_voters_from_csv

sms_service = SMSService()
whatsapp_service = WhatsAppService()

class PollingStationViewSet(viewsets.ModelViewSet):
    queryset = PollingStation.objects.all()
    serializer_class = PollingStationSerializer
    permission_classes = [RoleBasedPermission]

class VoterViewSet(viewsets.ModelViewSet):
    queryset = Voter.objects.all()
    serializer_class = VoterSerializer
    permission_classes = [RoleBasedPermission]

    @action(detail=True, methods=['get'])
    def message_history(self, request, pk=None):
        voter = self.get_object()
        messages = Message.objects.filter(voter=voter).order_by('created_at')
        serializer = MessageSerializer(messages, many=True)
        return response.Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='bulk_upload')
    def bulk_upload(self, request):
        """
        Upload a CSV file to create voters in bulk.

        Expected columns (headers, case-insensitive):
        name,id_number,phone_number,dob,r_g,clan,polling_station_name,location,age_group,football_club,status,notes
        """
        file = request.FILES.get('file')
        if not file:
            return response.Response(
                {"error": "Missing file"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_count, errors = import_voters_from_csv(file)

        return response.Response(
            {
                "created": created_count,
                "errors": errors,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['delete'], url_path='delete_all')
    def delete_all(self, request):
        """
        Danger: deletes ALL voters in the system.
        Intended for admin use to clear demo/test data.
        """
        deleted_count, _ = Voter.objects.all().delete()
        return response.Response(
            {"deleted": deleted_count},
            status=status.HTTP_200_OK,
        )

class SendMessageView(views.APIView):
    permission_classes = [RoleBasedPermission]

    def post(self, request):
        voter_id = request.data.get('voter_id')
        voter_ids = request.data.get('voter_ids') # For bulk
        channel = request.data.get('channel') # 'sms' or 'whatsapp'
        content = request.data.get('content')
        template_name = request.data.get('template_name')

        if voter_id:
            try:
                voter = Voter.objects.get(id=voter_id)
                if channel == 'sms':
                    msg, error = sms_service.send_sms(voter, content)
                elif channel == 'whatsapp':
                    if template_name:
                        msg, error = whatsapp_service.send_template_message(voter, template_name)
                    else:
                        msg, error = whatsapp_service.send_free_text(voter, content)
                else:
                    return response.Response({'error': 'Invalid channel'}, status=status.HTTP_400_BAD_REQUEST)

                if error:
                    return response.Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
                
                return response.Response(MessageSerializer(msg).data, status=status.HTTP_201_CREATED)
            except Voter.DoesNotExist:
                return response.Response({'error': 'Voter not found'}, status=status.HTTP_404_NOT_FOUND)

        elif voter_ids:
            voters = Voter.objects.filter(id__in=voter_ids)
            if channel == 'sms':
                results = sms_service.send_bulk_sms(voters, content)
                return response.Response({'results': results}, status=status.HTTP_200_OK)
            else:
                return response.Response({'error': 'Bulk not supported for this channel yet'}, status=status.HTTP_400_BAD_REQUEST)

        return response.Response({'error': 'Missing voter_id or voter_ids'}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class SMSWebhookView(views.APIView):
    def post(self, request):
        # Africa's Talking format
        from_number = request.data.get('from')
        text = request.data.get('text')
        
        if from_number and text:
            try:
                # Find voter by phone number (basic match)
                voter = Voter.objects.filter(phone_number__icontains=from_number[-9:]).first()
                if voter:
                    Message.objects.create(
                        voter=voter,
                        channel='sms',
                        content=text,
                        direction='inbound',
                        status='delivered'
                    )
                    
                    if text.strip().upper() == 'STOP':
                        voter.opted_in = False
                        voter.save()
                        
                return response.Response({'status': 'ok'}, status=status.HTTP_200_OK)
            except Exception as e:
                return response.Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return response.Response({'status': 'ignored'}, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class WhatsAppWebhookView(views.APIView):
    def get(self, request):
        # Meta Webhook verification
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        if mode == 'subscribe' and token == os.getenv('WHATSAPP_VERIFY_TOKEN'):
            return response.Response(int(challenge), status=status.HTTP_200_OK)
        return response.Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

    def post(self, request):
        data = request.data
        # Simplified Meta Payload Parsing
        try:
            entry = data.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            value = changes.get('value', {})
            messages = value.get('messages', [])
            
            if messages:
                msg = messages[0]
                from_number = msg.get('from')
                content = msg.get('text', {}).get('body')
                
                if from_number and content:
                    voter = Voter.objects.filter(phone_number__icontains=from_number[-9:]).first()
                    if voter:
                        Message.objects.create(
                            voter=voter,
                            channel='whatsapp',
                            content=content,
                            direction='inbound',
                            status='delivered'
                        )
            
            return response.Response({'status': 'ok'}, status=status.HTTP_200_OK)
        except Exception as e:
            return response.Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
