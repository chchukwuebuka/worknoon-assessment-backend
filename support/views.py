from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q
import json

from .models import Customer, Order, SupportRequest, Conversation, Message
from .serializers import (
    SupportRequestSerializer,
    SupportRequestHistorySerializer,
    ConversationSerializer,
    ConversationListSerializer,
    StartConversationSerializer,
    SendMessageSerializer,
)
from .services.ai_service import get_ai_support_response, get_ai_chat_response


def _get_customer_context(customer):
    """Build customer and order context strings."""
    customer_data = f"Name: {customer.name}\nID: {customer.customer_id}"
    order = Order.objects.filter(customer=customer).order_by('-purchase_date').first()
    if order:
        order_data = (
            f"Product: {order.product_name}\n"
            f"Amount: ${order.amount}\n"
            f"Date: {order.purchase_date}\n"
            f"Final Sale: {order.is_final_sale}\n"
            f"Damaged: {order.is_damaged}"
        )
    else:
        order_data = "No past orders found."
    return customer_data, order_data


def _find_customer(identifier):
    """Look up a customer by ID or name (case-insensitive)."""
    return Customer.objects.filter(
        Q(customer_id__iexact=identifier) | Q(name__iexact=identifier)
    ).first()


# ─── Legacy single-shot endpoint (kept for backward compat / tests) ───────────

class SupportRequestView(APIView):
    def post(self, request):
        serializer = SupportRequestSerializer(data=request.data)
        if serializer.is_valid():
            customer_id = serializer.validated_data['customer_id']
            message = serializer.validated_data['message']

            customer = _find_customer(customer_id)
            if not customer:
                return Response(
                    {"status": "error", "message": "Customer not found."}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            customer_data, order_data = _get_customer_context(customer)

            # Call AI Service
            ai_response_data = get_ai_support_response(customer_data, order_data, message)
            
            # Save request to db
            SupportRequest.objects.create(
                customer=customer,
                message=message,
                ai_response=json.dumps(ai_response_data)
            )

            return Response({
                "status": ai_response_data.get('decision', 'ESCALATED').lower(),
                "response": ai_response_data.get('reason', '')
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SupportHistoryView(APIView):
    def get(self, request):
        customer_id = request.query_params.get('customer_id')
        if not customer_id:
            return Response({"error": "customer_id query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        customer = _find_customer(customer_id)
        if not customer:
            return Response({"error": "Customer not found."}, status=status.HTTP_404_NOT_FOUND)

        requests = SupportRequest.objects.filter(customer=customer).order_by('-created_at')
        serializer = SupportRequestHistorySerializer(requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ─── Conversational chat endpoints ────────────────────────────────────────────

class StartConversationView(APIView):
    """POST /api/support/conversations/ — Start a new conversation."""
    def post(self, request):
        serializer = StartConversationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        identifier = serializer.validated_data['customer_id']
        user_message = serializer.validated_data['message']

        customer = _find_customer(identifier)
        if not customer:
            return Response(
                {"error": "Customer not found. Please check your Customer ID or Name."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Create conversation and first user message
        conversation = Conversation.objects.create(customer=customer)
        Message.objects.create(conversation=conversation, role='user', content=user_message)

        # Get AI response
        customer_data, order_data = _get_customer_context(customer)
        history = [{"role": "user", "content": user_message}]
        ai_reply = get_ai_chat_response(customer_data, order_data, history)

        # Save AI message
        Message.objects.create(conversation=conversation, role='assistant', content=ai_reply)

        # Return the full conversation
        out = ConversationSerializer(conversation).data
        return Response(out, status=status.HTTP_201_CREATED)


class ConversationMessageView(APIView):
    """POST /api/support/conversations/<id>/messages/ — Send a message in an existing conversation."""
    def get(self, request, conversation_id):
        """Retrieve the full conversation."""
        conversation = get_object_or_404(Conversation, id=conversation_id)
        out = ConversationSerializer(conversation).data
        return Response(out, status=status.HTTP_200_OK)

    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)
        serializer = SendMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_message = serializer.validated_data['message']

        # Save user message
        Message.objects.create(conversation=conversation, role='user', content=user_message)

        # Build full history for AI context
        all_messages = conversation.messages.order_by('created_at').values('role', 'content')
        history = list(all_messages)

        # Get AI response
        customer_data, order_data = _get_customer_context(conversation.customer)
        ai_reply = get_ai_chat_response(customer_data, order_data, history)

        # Save AI message
        Message.objects.create(conversation=conversation, role='assistant', content=ai_reply)

        # Touch updated_at
        conversation.save()

        out = ConversationSerializer(conversation).data
        return Response(out, status=status.HTTP_200_OK)


class ConversationListView(APIView):
    """GET /api/support/conversations/?customer_id=X — List conversations for a customer."""
    def get(self, request):
        customer_id = request.query_params.get('customer_id')
        if not customer_id:
            return Response(
                {"error": "customer_id query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        customer = _find_customer(customer_id)
        if not customer:
            return Response({"error": "Customer not found."}, status=status.HTTP_404_NOT_FOUND)

        conversations = Conversation.objects.filter(customer=customer).order_by('-updated_at')
        out = ConversationListSerializer(conversations, many=True).data
        return Response(out, status=status.HTTP_200_OK)
