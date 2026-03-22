from django.contrib import admin
from django.urls import path
from django_app.adapters.hello_views import hello_name
from django_app.adapters.product_views import (
    product_list,
    product_detail,
    product_bulk_create,
    product_bulk_csv,
    product_add_to_category,
)
from django_app.adapters.category_views import (
    category_list,
    category_detail,
    category_products,
)
from django_app.adapters.ui_views import (
    inventory_dashboard,
    ui_product_delete,
    ui_export_products,
)
from django_app.adapters.ai_inventory_views import (
    ai_scenario_dashboard,
    ai_generate_products,
    AIInventoryChatListView,
    AIInventoryChatDetailView,
    AIInventoryChatSyncView,
)
from django_app.adapters.search_views import (
    semantic_search_products,
    find_similar_products,
    hybrid_search,
)
from django_app.adapters.rag_views import (
    rag_chat_endpoint,
    generate_chat_title_endpoint,
)
from django_app.adapters.rag_chat_views import (
    RagChatListView,
    RagChatDetailView,
    RagChatSyncView,
)
from django_app.adapters.agent_views import (
    agent_chat,
    agent_chat_stream,
    search_products_for_quote,
    agent_status,
)
from django_app.adapters.agent_views import (
    QuoteAgentChatListView, QuoteAgentChatDetailView, QuoteAgentChatSyncView,
)

urlpatterns = [
    path("", inventory_dashboard, name="inventory_dashboard"),
    path("ui/products/<str:product_id>/delete/", ui_product_delete, name="ui_product_delete"),
    path("ui/products/export/", ui_export_products, name="ui_export_products"),

    path("ai/scenarios/", ai_scenario_dashboard, name="ai_scenario_dashboard"),
    path("ai/generate/", ai_generate_products, name="ai_generate_products"),
    path("ai/chats/", AIInventoryChatListView.as_view(), name="ai_inventory_chat_list"),
    path("ai/chats/sync/", AIInventoryChatSyncView.as_view(), name="ai_inventory_chat_sync"),
    path("ai/chats/<str:chat_id>/", AIInventoryChatDetailView.as_view(), name="ai_inventory_chat_detail"),

    path("search/semantic/", semantic_search_products, name="semantic_search"),
    path("search/similar/", find_similar_products, name="find_similar"),
    path("search/hybrid/", hybrid_search, name="hybrid_search"),

    path("rag/chat/", rag_chat_endpoint, name="rag_chat"),
    path("rag/generate-title/", generate_chat_title_endpoint, name="generate_chat_title"),
    path("rag/chats/", RagChatListView.as_view(), name="rag_chat_list"),
    path("rag/chats/sync/", RagChatSyncView.as_view(), name="rag_chat_sync"),
    path("rag/chats/<str:chat_id>/", RagChatDetailView.as_view(), name="rag_chat_detail"),

    path("agent/chat/", agent_chat, name="agent_chat"),
    path("agent/chat/stream/", agent_chat_stream, name="agent_chat_stream"),
    path("agent/search/", search_products_for_quote, name="search_products_for_quote"),
    path("agent/status/", agent_status, name="agent_status"),
    path("agent/chats/",            QuoteAgentChatListView.as_view()),
    path("agent/chats/sync/",       QuoteAgentChatSyncView.as_view()),
    path("agent/chats/<str:chat_id>/", QuoteAgentChatDetailView.as_view()),
    
    path("admin/", admin.site.urls),
    path("hello/", hello_name),
    path("products/", product_list),
    path("products/bulk/", product_bulk_create),
    path("products/bulk/csv/", product_bulk_csv),
    path("products/<str:product_id>/", product_detail),
    path("products/<str:product_id>/category/", product_add_to_category),
    path("categories/", category_list),
    path("categories/<str:category_id>/", category_detail),
    path("categories/<str:category_id>/products/", category_products),
]