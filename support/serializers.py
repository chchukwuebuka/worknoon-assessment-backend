from rest_framework import serializers
from .models import SupportRequest, Conversation, Message


class SupportRequestSerializer(serializers.Serializer):
    customer_id = serializers.CharField(max_length=100)
    message = serializers.CharField()


class SupportRequestHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportRequest
        fields = ['id', 'message', 'ai_response', 'created_at']


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'role', 'content', 'created_at']


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_id = serializers.CharField(source='customer.customer_id', read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'customer_name', 'customer_id', 'messages', 'created_at', 'updated_at']


class ConversationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing conversations (without full message history)."""
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_id = serializers.CharField(source='customer.customer_id', read_only=True)
    last_message = serializers.SerializerMethodField()
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'customer_name', 'customer_id', 'last_message', 'message_count', 'created_at', 'updated_at']

    def get_last_message(self, obj):
        last = obj.messages.order_by('-created_at').first()
        if last:
            return {'role': last.role, 'content': last.content[:100], 'created_at': last.created_at}
        return None

    def get_message_count(self, obj):
        return obj.messages.count()


class StartConversationSerializer(serializers.Serializer):
    customer_id = serializers.CharField(max_length=100)
    message = serializers.CharField()


class SendMessageSerializer(serializers.Serializer):
    message = serializers.CharField()
