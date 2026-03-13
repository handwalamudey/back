import africastalking
import os
from .models import Message

class SMSService:
    def __init__(self):
        self.username = os.getenv('AFRICASTALKING_USERNAME', 'sandbox')
        self.api_key = os.getenv('AFRICASTALKING_API_KEY')
        self.sender_id = os.getenv('AFRICASTALKING_SENDER_ID', 'NURDIN')
        
        if self.api_key:
            africastalking.initialize(self.username, self.api_key)
            self.sms = africastalking.SMS
        else:
            self.sms = None

    def send_sms(self, voter, content):
        if not voter.phone_number:
            return None, "Voter has no phone number"
        
        if not voter.opted_in:
            return None, "Voter has opted out"

        if not self.sms:
            # Handle sandbox/no-key mode for development
            print(f"[SMS SIMULATION] To: {voter.phone_number} | Msg: {content}")
            return Message.objects.create(
                voter=voter,
                channel='sms',
                content=content,
                direction='outbound',
                status='sent'
            ), None

        try:
            response = self.sms.send(content, [voter.phone_number], self.sender_id)
            # Assuming successfully sent if we get here
            # Response handling would be more detailed in production
            recipients = response['SMSMessageData']['Recipients']
            external_id = recipients[0]['messageId'] if recipients else None
            
            return Message.objects.create(
                voter=voter,
                channel='sms',
                content=content,
                direction='outbound',
                status='sent',
                external_id=external_id
            ), None
        except Exception as e:
            return None, str(e)

    def send_bulk_sms(self, voters, content):
        results = []
        for voter in voters:
            msg, error = self.send_sms(voter, content)
            results.append({'voter_id': voter.id, 'success': msg is not None, 'error': error})
        return results
