import os
import sys
import anthropic
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_anthropic_connection():
    """Test function to verify Anthropic API connection works"""
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not found in environment variables")
        return False
        
    logger.info(f"API key found: {api_key[:4]}...{api_key[-4:]}")
    
    try:
        # Initialize client
        logger.info("Initializing Anthropic client...")
        client = anthropic.Anthropic(api_key=api_key)
        
        # Make a simple API call
        logger.info("Making test API call...")
        message = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=20,
            temperature=0,
            messages=[
                {"role": "user", "content": "Say hello in one word"}
            ]
        )
        
        # Extract response
        response = message.content[0].text
        logger.info(f"Test API call successful. Response: {response}")
        return True
        
    except Exception as e:
        logger.error(f"Error testing Anthropic API: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = test_anthropic_connection()
    if success:
        logger.info("✅ Anthropic API connection test passed")
        sys.exit(0)
    else:
        logger.error("❌ Anthropic API connection test failed")
        sys.exit(1) 