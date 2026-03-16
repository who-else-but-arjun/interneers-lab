import google.generativeai as genai
import os

GEMINI_API_KEY = "API_KEY"

genai.configure(api_key=GEMINI_API_KEY)

def generate_product_names(temperature=0.0):
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    prompt = "Generate 5 creative product names for a toy store. Return them as a simple numbered list."
    
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=100
        )
    )
    
    return response

def count_tokens(text):
    model = genai.GenerativeModel("gemini-2.5-flash")
    return model.count_tokens(text)

def main():
    print("=" * 60)
    print("TASK 1: Generate Product Names with Gemini")
    print("=" * 60)
    
    print("\n--- Temperature = 0.0 (Deterministic) ---")
    response_0 = generate_product_names(temperature=0.0)
    print("Raw Response:")
    print(response_0.text)
    
    input_tokens_0 = count_tokens("Generate 5 creative product names for a toy store. Return them as a simple numbered list.")
    output_tokens_0 = count_tokens(response_0.text)
    print(f"\nTokens Used:")
    print(f"  Input tokens: {input_tokens_0.total_tokens}")
    print(f"  Output tokens: {output_tokens_0.total_tokens}")
    
    print("\n--- Temperature = 1.0 (Balanced) ---")
    response_1 = generate_product_names(temperature=1.0)
    print("Raw Response:")
    print(response_1.text)
    
    input_tokens_1 = count_tokens("Generate 5 creative product names for a toy store. Return them as a simple numbered list.")
    output_tokens_1 = count_tokens(response_1.text)
    print(f"\nTokens Used:")
    print(f"  Input tokens: {input_tokens_1.total_tokens}")
    print(f"  Output tokens: {output_tokens_1.total_tokens}")
    
    print("\n--- Temperature = 1.5 (Creative/Random) ---")
    response_15 = generate_product_names(temperature=1.5)
    print("Raw Response:")
    print(response_15.text)
    
    input_tokens_15 = count_tokens("Generate 5 creative product names for a toy store. Return them as a simple numbered list.")
    output_tokens_15 = count_tokens(response_15.text)
    print(f"\nTokens Used:")
    print(f"  Input tokens: {input_tokens_15.total_tokens}")
    print(f"  Output tokens: {output_tokens_15.total_tokens}")
    
    print("\n" + "=" * 60)
    print("OBSERVATIONS:")
    print("=" * 60)
    print("Temperature 0.0: Most consistent, repeatable results")
    print("Temperature 1.0: Balanced creativity with coherence")
    print("Temperature 1.5: More varied, potentially surprising results")
    print("\nNote: Gemini 2.5 Flash is FREE tier available!")
    print("Cost for this run: $0.00 (using free tier)")
    print("=" * 60)

if __name__ == "__main__":
    main()
