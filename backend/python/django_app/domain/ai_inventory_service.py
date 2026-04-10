import json
import os
from typing import Optional, Dict, Any, List, Tuple

import google.genai as genai
from google.genai import types

from django_app.domain import product_service

# Configure Gemini API from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class AIInventoryService:
    """Service class for AI inventory operations"""
    
    @staticmethod
    def process_ai_chat(user_message: str, max_count: int = 10, chat_history: Optional[List] = None) -> Dict[str, Any]:
        """
        Process AI chat request and generate response
        
        Args:
            user_message: The user's message
            max_count: Maximum number of products to generate
            chat_history: Previous chat history
            
        Returns:
            Dictionary containing AI response with intent, message, and products
        """
        if not GEMINI_API_KEY:
            return {
                "intent": "chat",
                "message": "AI service is not configured. Please set GEMINI_API_KEY environment variable.",
                "products": []
            }
        
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Get current inventory information
        db_info = ""
        try:
            summary = AIInventoryService.get_inventory_summary()
            db_info = f"""Current Inventory Status:
- Total Products: {summary.get('total_products', 'N/A')}
- Total Value: ₹{summary.get('total_value', 0):,.0f}
- Low Stock Items: {summary.get('low_stock_count', 0)}"""
        except Exception:
            pass
        
        prompt = f'''You are an AI assistant for inventory management. Your ONLY job is to understand user intent and generate product data when requested.

--- LIVE INVENTORY DATA ---

{db_info}

--- END INVENTORY DATA ---

--- CHAT HISTORY ---

{json.dumps(chat_history[-5:] if chat_history else [], indent=2)}

--- END CHAT HISTORY ---

User message: "{user_message}"
Maximum products to generate: {max_count}

Your capabilities:
1. Generate/create/add products to inventory (product_generation intent)
2. General chat that is NOT about policies/warranties/returns (chat intent)

Examples of product_generation intent:
- "Create 20 electronics items"
- "Add some office supplies"
- "Generate furniture products"
- "I need 15 sports items"

Examples of chat intent:
- "Hello" / "What can you do?"
- "How many products do I have?" (use inventory data above)
- "What's my total inventory value?" (use inventory data above)

Respond with ONLY a valid JSON object in this exact format:
{{
    "intent": "product_generation" or "chat",
    "message": "A friendly response. For product generation, confirm what you're creating. For chat intent about policies/warranties/returns, redirect to RAG Chat.",
    "products": [array of products if intent is product_generation, otherwise empty array]
}}

Each product must have these exact fields:
- name: string
- description: string
- category: string
- price: float (INR - realistic)
- brand: string
- quantity: integer

STRICT REQUIREMENTS:
1. **PRIORITY - CHECK USER MESSAGE FOR QUANTITY**: Before using the "Maximum products to generate" value above, CHECK if the user explicitly mentioned a number in their message. 
   - If user says "Create 20 electronics" → generate 20 products (ignore the max_count above, use 20)
   - If user says "I need 15 items" → generate 15 products
   - If user says "Generate 50 products" → generate 50 products (or max 50)
   - ONLY use the max_count value if user didn't specify a quantity in their message
2. The maximum products you can generate is 50. Never exceed 50 even if user asks for more.
3. When user asks for N products, you MUST generate EXACTLY N products in the products array - no more, no less.
4. Do NOT generate just 1 product when the user asks for multiple. Always match the requested quantity.
5. Use realistic Indian market prices (INR) for all products.
6. Use realistic brand names that exist in the real world.

CRITICAL OUTPUT RULES:
- Return ONLY the raw JSON object
- NO markdown code blocks (no ```json or ```)
- NO markdown formatting of any kind
- NO extra text before or after the JSON'''
        
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=8192
                )
            )
            
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            elif text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {
                    "intent": "chat",
                    "message": "I'm not sure I understood that. You can ask me to generate products by saying something like 'Create 20 electronics items' or just chat with me!",
                    "products": []
                }
        except Exception as e:
            return {
                "intent": "chat",
                "message": f"AI service error: {str(e)}",
                "products": []
            }
    
    @staticmethod
    def get_inventory_summary() -> Dict[str, Any]:
        """
        Get current inventory summary
        
        Returns:
            Dictionary containing inventory statistics
        """
        try:
            products, _ = product_service.list_products(page=1, page_size=1000, category_ids=None)
            total_value = sum((p.price or 0) * (p.quantity or 0) for p in products)
            low_stock = sum(1 for p in products if (p.quantity or 0) < 50)
            
            categories = {}
            for p in products:
                categories[p.category] = categories.get(p.category, 0) + 1
            
            return {
                "total_products": len(products),
                "total_value": total_value,
                "low_stock_count": low_stock,
                "categories": categories
            }
        except Exception as e:
            # Return default values if there's an error
            return {
                "total_products": 0,
                "total_value": 0,
                "low_stock_count": 0,
                "categories": {}
            }