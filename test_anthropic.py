import os
import sys
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
    
    # Try to initialize the client
    client = None
    
    try:
        print("\nAttempting to import Anthropic SDK...")
        import anthropic
        print(f"✓ Anthropic SDK imported (version: {anthropic.__version__ if hasattr(anthropic, '__version__') else 'unknown'})")
        
        # Super simple initialization with just the API key
        print("\nInitializing Anthropic client with minimal parameters...")
        client = anthropic.Anthropic(api_key=api_key)
        print("✓ Client initialized successfully")
        
        # Create message parameters
        message_params = {
            "model": "claude-3-7-sonnet-20250219",
            "max_tokens": 100,
            "temperature": 0,
            "messages": [
                {"role": "user", "content": "Please respond with 'API connection successful!' if you can read this message."}
            ]
        }
        
        # Test the API call
        print("\nSending test message to API...")
        try:
            response = client.messages.create(**message_params)
            response_text = response.content[0].text
            
            print("\nAPI Response:")
            print(response_text)
            print("\n✅ Anthropic API test completed successfully!")
            return True
            
        except Exception as e:
            print(f"\nERROR during API call: {str(e)}", file=sys.stderr)
            print(f"Exception type: {type(e).__name__}")
            print(f"Exception args: {e.args}")
            print("\n❌ API call failed")
            return False
            
    except ImportError as e:
        print(f"\nERROR: Failed to import Anthropic SDK: {str(e)}", file=sys.stderr)
        print("Try installing the SDK: pip install anthropic==0.18.1")
        return False
    except Exception as e:
        print(f"\nERROR: Unexpected error during client initialization: {str(e)}", file=sys.stderr)
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception args: {e.args}")
        print("\nPossible solutions:")
        print("1. Check if your API key is valid and has not expired")
        print("2. Verify you have the required Anthropic SDK version (try: pip install anthropic==0.18.1)")
        print("3. Check if your internet connection can reach the Anthropic API")
        print("4. Ensure your API key has sufficient credits/quota")
        print("\n❌ Anthropic API test failed")
        return False

if __name__ == "__main__":
    test_anthropic_connection() 