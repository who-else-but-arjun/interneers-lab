import google.genai as genai
import json
import sys
import os
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class ProductModel(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=500)
    category: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)
    brand: str = Field(..., min_length=1, max_length=100)
    quantity: int = Field(..., ge=0)
    category_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @validator('price')
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        return round(v, 2)

    @validator('quantity')
    def quantity_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError('Quantity must be 0 or greater')
        return int(v)

    @validator('name', 'brand', 'category')
    def must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()

class ProductList(BaseModel):
    products: List[ProductModel]

def generate_products_with_gemini(count=10):
    if not GEMINI_API_KEY:
        return "Error: GEMINI_API_KEY not set"
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""Generate {count} products for a toy store inventory.
Return ONLY a valid JSON array with no markdown formatting.

Each product must have these exact fields:
- name: string (product name)
- description: string (brief description)
- category: string (product category)
- price: float (price in USD, between 5.0 and 200.0)
- brand: string (brand name)
- quantity: integer (stock quantity between 0 and 1000)

Output format: [{{"name": "...", "description": "...", "category": "...", "price": 29.99, "brand": "...", "quantity": 100}}, ...]"""
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=genai.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=8192
        )
    )
    
    return response.text

def clean_json_response(text):
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def validate_and_save_products(json_data):
    try:
        cleaned_data = clean_json_response(json_data)
        raw_products = json.loads(cleaned_data)
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return []
    
    valid_products = []
    invalid_products = []
    
    for idx, prod_data in enumerate(raw_products):
        try:
            prod_data['created_at'] = datetime.utcnow().isoformat()
            prod_data['updated_at'] = datetime.utcnow().isoformat()
            
            product = ProductModel(**prod_data)
            valid_products.append(product.dict())
        except Exception as e:
            invalid_products.append({
                "index": idx,
                "data": prod_data,
                "error": str(e)
            })
            
    if invalid_products:
        print("\nInvalid product errors:")
        for inv in invalid_products:
            print(f"  Product {inv['index']}: {inv['error']}")
    
    if valid_products:
        print("\nSample valid product:")
        print(json.dumps(valid_products[0], indent=2))
        
        output_file = "validated_products.json"
        with open(output_file, "w") as f:
            json.dump(valid_products, f, indent=2)
        print(f"\nSaved {len(valid_products)} validated products to {output_file}")
        
        print("\nAttempting to save to MongoDB...")
        save_to_mongodb(valid_products)
    
    return valid_products, invalid_products

def save_to_mongodb(products):
    try:
        from mongoengine import connect, disconnect, Document, StringField, FloatField, IntField, DateTimeField
        
        disconnect(alias='default')
        connect('inventory_db', host='mongodb://localhost:27017/', alias='default')
        
        class ProductDocument(Document):
            name = StringField(required=True)
            description = StringField()
            category = StringField(required=True)
            price = FloatField(required=True, min_value=0.01)
            brand = StringField(required=True)
            quantity = IntField(required=True, min_value=0)
            category_id = StringField()
            created_at = DateTimeField()
            updated_at = DateTimeField()
            
            meta = {'collection': 'products'}
        
        inserted_count = 0
        for prod in products:
            product_doc = ProductDocument(
                name=prod['name'],
                description=prod['description'],
                category=prod['category'],
                price=prod['price'],
                brand=prod['brand'],
                quantity=prod['quantity'],
                category_id=prod.get('category_id'),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            product_doc.save()
            inserted_count += 1
        
        print(f"Successfully saved {inserted_count} products to MongoDB")
        return inserted_count
        
    except Exception as e:
        print(f"MongoDB save error: {e}")
        print("Products validated but not saved to database (connection may not be available)")
        return 0

def main():
    print("=" * 70)
    print("TASK 3: Pydantic Validation for LLM-Generated Products")
    print("=" * 70)
    
    print("\nGenerating 10 products with Gemini...")
    raw_response = generate_products_with_gemini(count=10)
    print(f"Received response ({len(raw_response)} characters)")
    
    print("\nValidating products with Pydantic...")
    valid_products, invalid_products = validate_and_save_products(raw_response)
    
    print(f"\nValidation Results:")
    print(f"  Valid products: {len(valid_products)}")
    print(f"  Invalid products: {len(invalid_products)}")
    
    print("\n" + "=" * 70)
    print("TASK 3 COMPLETED")
    print("=" * 70)

if __name__ == "__main__":
    main()
