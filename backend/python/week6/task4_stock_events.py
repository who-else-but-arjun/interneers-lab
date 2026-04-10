import google.genai as genai
import json
import sys
import os
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, validator
from typing import Optional, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class StockEvent(BaseModel):
    event_type: str = Field(..., min_length=1, max_length=50)
    product_name: str = Field(..., min_length=1, max_length=200)
    expected_date: str = Field(..., min_length=1, max_length=20)
    quantity_change: int = Field(...)
    description: str = Field(..., min_length=1, max_length=300)
    priority: str = Field(..., min_length=1, max_length=20)

    @validator('event_type')
    def valid_event_type(cls, v):
        valid_types = ['Delivery', 'Restock', 'Sale', 'Return', 'Audit', 'Expiry', 'Reorder']
        if v not in valid_types:
            raise ValueError(f'Event type must be one of: {valid_types}')
        return v

    @validator('priority')
    def valid_priority(cls, v):
        valid_priorities = ['Low', 'Medium', 'High', 'Critical']
        if v not in valid_priorities:
            raise ValueError(f'Priority must be one of: {valid_priorities}')
        return v

class StockEventList(BaseModel):
    events: List[StockEvent]

def generate_stock_events():
    if not GEMINI_API_KEY:
        return "Error: GEMINI_API_KEY not set"
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    today = datetime.now()
    future_dates = [(today + timedelta(days=i*3)).strftime("%b %d, %Y") for i in range(1, 11)]
    
    prompt = f"""Generate 10 realistic future stock events for store inventory.

Return ONLY a valid JSON array with no markdown formatting.

Each event must have these exact fields:
- event_type: string (must be one of: Delivery, Restock, Sale, Return, Audit, Expiry, Reorder)
- product_name: string (a toy product name)
- expected_date: string (date in format "MMM DD, YYYY")
- quantity_change: integer (positive for incoming stock, negative for outgoing)
- description: string (brief description of the event)
- priority: string (must be one of: Low, Medium, High, Critical)

Use these specific dates in order: {', '.join(future_dates[:5])} and continue the pattern for the remaining 5.

Example output:
[
  {{
    "event_type": "Delivery",
    "product_name": "Lego Castle Set",
    "expected_date": "{future_dates[0]}",
    "quantity_change": 50,
    "description": "Expected delivery from supplier",
    "priority": "High"
  }}
]

Generate diverse events including deliveries, sales, returns, audits, and reorders."""
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=genai.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=2048
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

def validate_events(json_data):
    try:
        cleaned_data = clean_json_response(json_data)
        raw_events = json.loads(cleaned_data)
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return [], []
    
    valid_events = []
    invalid_events = []
    
    for idx, event_data in enumerate(raw_events):
        try:
            event = StockEvent(**event_data)
            valid_events.append(event.dict())
        except Exception as e:
            invalid_events.append({
                "index": idx,
                "data": event_data,
                "error": str(e)
            })
    
    return valid_events, invalid_events

def simulate_audit_trail(events):
    audit_log = []
    
    for event in events:
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": event['event_type'],
            "product_name": event['product_name'],
            "expected_date": event['expected_date'],
            "quantity_change": event['quantity_change'],
            "description": event['description'],
            "priority": event['priority'],
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }
        audit_log.append(audit_entry)
    
    return audit_log

def main():
    print("=" * 70)
    print("TASK 4: Generate Future Stock Events for Audit Trail Testing")
    print("=" * 70)
    
    print("\nGenerating 10 future stock events with Gemini...")
    raw_response = generate_stock_events()
    print(f"Received response ({len(raw_response)} characters)")
    
    print("\nValidating events with Pydantic...")
    valid_events, invalid_events = validate_events(raw_response)
    
    print(f"\nValidation Results:")
    print(f"  Valid events: {len(valid_events)}")
    print(f"  Invalid events: {len(invalid_events)}")
    
    if invalid_events:
        print("\nInvalid event errors:")
        for inv in invalid_events:
            print(f"  Event {inv['index']}: {inv['error']}")
    
    if valid_events:
        print("\n" + "-" * 70)
        print("GENERATED STOCK EVENTS:")
        print("-" * 70)
        
        for idx, event in enumerate(valid_events, 1):
            print(f"\n{idx}. [{event['priority']}] {event['event_type']}")
            print(f"   Product: {event['product_name']}")
            print(f"   Date: {event['expected_date']}")
            print(f"   Quantity Change: {event['quantity_change']:+d}")
            print(f"   Description: {event['description']}")
        
        print("\n" + "-" * 70)
        print("SIMULATING AUDIT TRAIL...")
        print("-" * 70)
        
        audit_log = simulate_audit_trail(valid_events)
        
        print(f"\nCreated {len(audit_log)} audit trail entries")
        print("\nSample audit entry:")
        print(json.dumps(audit_log[0], indent=2))
        
        events_file = "stock_events.json"
        with open(events_file, "w") as f:
            json.dump(valid_events, f, indent=2)
        
        audit_file = "audit_trail.json"
        with open(audit_file, "w") as f:
            json.dump(audit_log, f, indent=2)
        
        print(f"\nSaved {len(valid_events)} events to {events_file}")
        print(f"Saved {len(audit_log)} audit entries to {audit_file}")
    
    print("\n" + "=" * 70)
    print("TASK 4 COMPLETED - Audit Trail Logic Validated")
    print("=" * 70)

if __name__ == "__main__":
    main()
