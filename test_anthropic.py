import os
import sys
import anthropic
from dotenv import load_dotenv

def test_anthropic_connection():
    """
    Tests the Anthropic API connection to diagnose issues
    """
    print("Testing Anthropic API connection...")
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Get API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("ERROR: No Anthropic API key found. Make sure ANTHROPIC_API_KEY is set in your .env file.", file=sys.stderr)
        return False
    
    print(f"✓ API key found (starts with {api_key[:8]}...)")
    
    try:
        # Initialize client with API version
        client = anthropic.Anthropic(
            api_key=api_key,
            default_headers={"anthropic-version": "2023-06-01"}
        )
        print("✓ Client initialized successfully")
        
        # Test with a simple message
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=100,
            temperature=0,
            messages=[
                {"role": "user", "content": "Please respond with 'API connection successful!' if you can read this message."}
            ]
        )
        
        print("\nAPI Response:")
        print(response.content[0].text)
        print("\n✅ Anthropic API test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\nERROR: {str(e)}", file=sys.stderr)
        print("\nPossible solutions:")
        print("1. Check if your API key is valid and has not expired")
        print("2. Verify you have the required Anthropic SDK version (try: pip install anthropic==0.19.1)")
        print("3. Check if your internet connection can reach the Anthropic API")
        print("4. Ensure your API key has sufficient credits/quota")
        print("\n❌ Anthropic API test failed")
        return False

if __name__ == "__main__":
    test_anthropic_connection() 