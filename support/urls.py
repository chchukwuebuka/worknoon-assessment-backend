from django.urls import path
from .views import (
    SupportRequestView,
    SupportHistoryView,
    StartConversationView,
    ConversationMessageView,
    ConversationListView,
)

urlpatterns = [
    # Legacy single-shot endpoints
    path('', SupportRequestView.as_view(), name='support-request'),
    path('history/', SupportHistoryView.as_view(), name='support-history'),

    # Conversational chat endpoints
    path('conversations/', StartConversationView.as_view(), name='start-conversation'),
    path('conversations/list/', ConversationListView.as_view(), name='conversation-list'),
    path('conversations/<int:conversation_id>/messages/', ConversationMessageView.as_view(), name='conversation-messages'),
]
