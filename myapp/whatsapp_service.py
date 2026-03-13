import requests
import os
import json
from .models import Message

class WhatsAppService:
    def __init__(self):
        self.api_token = os.getenv('WHATSAPP_API_TOKEN')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.version = os.getenv('WHATSAPP_API_VERSION', 'v17.0')
        self.api_url = f"https://graph.facebook.com/{self.version}/{self.phone_number_id}/messages"

    def send_template_message(self, voter, template_name, language_code="en", components=None):
        if not voter.phone_number:
            return None, "Voter has no phone number"

        if not self.api_token:
            print(f"[WHATSAPP SIMULATION] Template: {template_name} to {voter.phone_number}")
            return Message.objects.create(
                voter=voter,
                channel='whatsapp',
                content=f"Template: {template_name}",
                direction='outbound',
                status='sent'
            ), None

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": voter.phone_number.replace('+', ''),
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code}
            }
        }
        
        if components:
            payload["template"]["components"] = components

        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            data = response.json()
            if response.status_code == 200:
                external_id = data['messages'][0]['id']
                return Message.objects.create(
                    voter=voter,
                    channel='whatsapp',
                    content=f"Template: {template_name}",
                    direction='outbound',
                    status='sent',
                    external_id=external_id
                ), None
            else:
                return None, data.get('error', {}).get('message', 'Unknown error')
        except Exception as e:
            return None, str(e)

    def send_free_text(self, voter, content):
        # Note: This only works within the 24-hour service window
        if not voter.phone_number:
            return None, "Voter has no phone number"

        if not self.api_token:
            print(f"[WHATSAPP SIMULATION] Free Text: {content} to {voter.phone_number}")
            return Message.objects.create(
                voter=voter,
                channel='whatsapp',
                content=content,
                direction='outbound',
                status='sent'
            ), None

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": voter.phone_number.replace('+', ''),
            "type": "text",
            "text": {"body": content}
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            data = response.json()
            if response.status_code == 200:
                external_id = data['messages'][0]['id']
                return Message.objects.create(
                    voter=voter,
                    channel='whatsapp',
                    content=content,
                    direction='outbound',
                    status='sent',
                    external_id=external_id
                ), None
            else:
                return None, data.get('error', {}).get('message', 'Unknown error')
        except Exception as e:
            return None, str(e)
