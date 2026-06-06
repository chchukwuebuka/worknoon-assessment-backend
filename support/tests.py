from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch
from datetime import datetime, timedelta
import json

from support.models import Customer, Order, SupportRequest

class SupportAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create test customer
        self.customer = Customer.objects.create(
            customer_id="CUST999",
            name="Alice Test"
        )
        
        # Create a basic order
        self.order = Order.objects.create(
            customer=self.customer,
            product_name="Gadget",
            amount=150.00,
            purchase_date=datetime.now().date() - timedelta(days=5),
            is_final_sale=False,
            is_damaged=False
        )
        
        self.submit_url = reverse('support-request')
        self.history_url = reverse('support-history')

    @patch('support.views.get_ai_support_response')
    def test_submit_request_approved(self, mock_ai_response):
        # Mock AI response
        mock_ai_response.return_value = {
            "decision": "APPROVED",
            "reason": "Refund approved because order is within 14 days."
        }
        
        payload = {
            "customer_id": "CUST999",
            "message": "I want a refund."
        }
        
        response = self.client.post(self.submit_url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'approved')
        self.assertEqual(response.data['response'], "Refund approved because order is within 14 days.")
        
        # Verify db record
        self.assertTrue(SupportRequest.objects.filter(customer=self.customer).exists())

    @patch('support.views.get_ai_support_response')
    def test_submit_request_by_name(self, mock_ai_response):
        # Mock AI response
        mock_ai_response.return_value = {
            "decision": "APPROVED",
            "reason": "Refund approved because order is within 14 days."
        }
        
        payload = {
            "customer_id": "Alice Test",
            "message": "I want a refund."
        }
        
        response = self.client.post(self.submit_url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'approved')
        self.assertEqual(response.data['response'], "Refund approved because order is within 14 days.")

    @patch('support.views.get_ai_support_response')
    def test_submit_request_denied(self, mock_ai_response):
        # Make the order final sale
        self.order.is_final_sale = True
        self.order.save()
        
        mock_ai_response.return_value = {
            "decision": "DENIED",
            "reason": "Final sale items cannot be refunded."
        }
        
        payload = {
            "customer_id": "CUST999",
            "message": "I want a refund."
        }
        
        response = self.client.post(self.submit_url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'denied')
        self.assertEqual(response.data['response'], "Final sale items cannot be refunded.")

    @patch('support.views.get_ai_support_response')
    def test_submit_request_escalated(self, mock_ai_response):
        # Make the order above $500
        self.order.amount = 600.00
        self.order.save()
        
        mock_ai_response.return_value = {
            "decision": "ESCALATED",
            "reason": "Request involves an order over $500. Escalating to human."
        }
        
        payload = {
            "customer_id": "CUST999",
            "message": "I want a refund."
        }
        
        response = self.client.post(self.submit_url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'escalated')

    def test_submit_request_customer_not_found(self):
        payload = {
            "customer_id": "INVALID",
            "message": "Help me."
        }
        response = self.client.post(self.submit_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_history_missing_customer_id(self):
        response = self.client.get(self.history_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_history_customer_not_found(self):
        response = self.client.get(f"{self.history_url}?customer_id=INVALID")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_history_success(self):
        # Add support requests
        SupportRequest.objects.create(
            customer=self.customer,
            message="Request 1",
            ai_response=json.dumps({"decision": "APPROVED", "reason": "reason 1"})
        )
        SupportRequest.objects.create(
            customer=self.customer,
            message="Request 2",
            ai_response=json.dumps({"decision": "DENIED", "reason": "reason 2"})
        )
        
        response = self.client.get(f"{self.history_url}?customer_id=CUST999")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['message'], "Request 2") # Ordered by -created_at
