import os
from flask import Flask, render_template, request, jsonify
import logging
import sys
from flask_cors import CORS
from dotenv import load_dotenv

'''
Railway Deployment Configuration:
---------------------------------
For best results with Railway deployment, add the following environment variables in the Railway dashboard:
- HTTP_PROXY=""
- HTTPS_PROXY=""
- NO_PROXY="*"

These settings will help prevent proxy-related errors when connecting to the Anthropic API.
'''

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Clear proxy environment variables - Railway specific fix
# This needs to happen BEFORE importing anthropic
logger.info("Clearing proxy environment variables to avoid Railway proxy issues")
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['NO_PROXY'] = '*'

# Now it's safe to import Anthropic
import anthropic

# Load environment variables
load_dotenv()

# Initialize the Flask application
app = Flask(__name__)
CORS(app)

# Initialize the Anthropic client as a global variable
client = None

# Try to initialize the Anthropic client
try:
    # Get API key from environment variable
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    
    logger.info("Attempting to initialize Anthropic client...")
    
    # SIMPLIFIED: Try just ONE method with minimal parameters
    try:
        # Only use the absolute minimal parameters required
        import anthropic
        logger.info("Imported Anthropic version: " + getattr(anthropic, "__version__", "unknown"))
        
        # Applying monkey patching to handle both older and newer SDK versions
        # In newer versions, there might be a separate Client class
        
        # Ensure we have a clean set of parameters for initialization
        safe_params = {"api_key": api_key}
        
        # Create a custom session with explicitly empty proxies
        try:
            import requests
            logger.info("Setting up custom HTTP session with empty proxies")
            
            # Configure a session with no proxies
            session = requests.Session()
            session.proxies = {}
            
            # Add this session to the initialization parameters if possible
            if hasattr(anthropic, 'Client') and hasattr(anthropic.Client, "create_http_client"):
                logger.info("Adding custom HTTP session to Anthropic client params")
                safe_params["http_client"] = session
        except Exception as session_error:
            logger.warning(f"Could not set up custom HTTP session: {str(session_error)}")
        
        # Try to identify the exact client class structure
        try:
            # Try to find the Client class if it exists in newer SDK versions
            if hasattr(anthropic, 'Client'):
                logger.info("Found anthropic.Client class - patching it")
                # Patch the Client class init
                original_client_init = anthropic.Client.__init__
                
                def patched_client_init(self, *args, **kwargs):
                    # Log original kwargs for debugging
                    logger.info(f"Original Client init params: {list(kwargs.keys())}")
                    
                    # Remove problematic parameters
                    for param in ['proxies']:
                        if param in kwargs:
                            logger.info(f"Removing '{param}' parameter from Client initialization")
                            del kwargs[param]
                    
                    # Call original init with clean kwargs
                    return original_client_init(self, *args, **kwargs)
                
                # Apply the patch
                anthropic.Client.__init__ = patched_client_init
            
            # Also patch the Anthropic class for backward compatibility
            original_anthropic_init = anthropic.Anthropic.__init__
            
            def patched_anthropic_init(self, *args, **kwargs):
                # Log original kwargs for debugging
                logger.info(f"Original Anthropic init params: {list(kwargs.keys())}")
                
                # Remove problematic parameters
                for param in ['proxies']:
                    if param in kwargs:
                        logger.info(f"Removing '{param}' parameter from Anthropic initialization")
                        del kwargs[param]
                
                # Call original init with clean kwargs
                return original_anthropic_init(self, *args, **kwargs)
            
            # Apply the patch
            anthropic.Anthropic.__init__ = patched_anthropic_init
            
            logger.info("Applied patches to Anthropic client classes to filter unwanted parameters")
            
        except Exception as patch_error:
            # If patching fails, log the error but continue with a simple initialization
            logger.error(f"Error applying patches: {str(patch_error)}")
        
        # Try different initialization approaches in order of preference
        client = None
        
        # Attempt initialization with just the essential parameters
        try:
            logger.info("Attempting to initialize with clean parameters")
            client = anthropic.Anthropic(**safe_params)
            logger.info("Successfully initialized Anthropic client with clean parameters")
        except Exception as init_error:
            logger.error(f"Error in first initialization attempt: {str(init_error)}")
            
            # If that fails, try with Client class if available
            if hasattr(anthropic, 'Client'):
                try:
                    logger.info("Attempting to initialize with Client class")
                    client = anthropic.Client(**safe_params)
                    logger.info("Successfully initialized Client")
                except Exception as client_error:
                    logger.error(f"Error initializing with Client class: {str(client_error)}")
                    
                    # Try with http_session parameter naming instead of http_client
                    try:
                        logger.info("Attempting with http_session parameter")
                        modified_params = safe_params.copy()
                        
                        # Replace http_client with http_session if it exists
                        if 'http_client' in modified_params:
                            modified_params['http_session'] = modified_params.pop('http_client')
                            
                        client = anthropic.Client(**modified_params)
                        logger.info("Successfully initialized Client with http_session")
                    except Exception as session_error:
                        logger.error(f"Error initializing with http_session: {str(session_error)}")
                        
                        # One last attempt with base_url parameter to bypass proxy issues
                        try:
                            logger.info("Attempting direct API URL specification")
                            final_params = {"api_key": api_key, "base_url": "https://api.anthropic.com"}
                            client = anthropic.Client(**final_params)
                            logger.info("Successfully initialized Client with explicit base_url")
                        except Exception as url_error:
                            logger.error(f"Error initializing with explicit base_url: {str(url_error)}")
            
            # If all attempts fail, we have no choice but to let the normal initialization fail
            if client is None:
                raise Exception("Failed to initialize client with any approach")
        
        logger.info("Anthropic client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Anthropic client: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception args: {e.args}")
        raise Exception(f"Failed to initialize Anthropic client: {str(e)}")
    
except Exception as e:
    logger.error(f"Error initializing Anthropic client: {str(e)}")
    # We continue app initialization even if client fails,
    # to allow the app to start and provide error messages

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/putter-info', methods=['POST'])
def get_putter_info():
    # Get the putter name from the request
    data = request.json
    putter_name = data.get('putter_name', '')
    
    if not putter_name:
        return jsonify({"error": "Please provide a putter name"}), 400
    
    # Check if client is initialized
    if client is None:
        return jsonify({"error": "Anthropic client not initialized properly"}), 500
    
    try:
        logger.info(f"Making API call for putter: {putter_name}")
        
        # Create the message parameters
        message_params = {
            "model": "claude-3-7-sonnet-20250219",
            "max_tokens": 8192,
            "temperature": 1,
            "messages": [
                {
                    "role": "user",
                    "content": putter_name
                }
            ]
        }
        
        # Add the system prompt in a way that's compatible with different versions
        system_prompt = "#Your Role\nYou are a golf equipment expert specializing in Scotty Cameron putters. Your task is to research and analyze the current market value and key features of a specific Scotty Cameron putter model that will be provided to you by the user.\n\n#Your Task\nGiven the name of a Scotty Cameron putter do deep research on the pricing and specification for the specific putter you are prompted with. Your data will be used to provide important pricing data to users so make sure you research this specific make and model of the putter and focus your research to information specific to the putter you are prompted with. \n\n#Writing Behaviors\nYour writing should not be flowery. Stick to objective facts about the putter. \n\n#Response Format\n- Format your response as a detailed report beginning with a brief overview of the putter and then go through the research parameter sections \n- have the response be in clear sections and include as many specific details as possible. \n\n# Research Parameters\nFor this model, provide a comprehensive analysis including:\n**Basic Information**\n   - Year of release\n   - Model family/line (e.g., Newport, Phantom X, Special Select, TeI3, etc.)\n   - Original retail price (if available)\n   - Type (blade, mid-mallet, mallet)\n   - Production status (standard release, limited edition, tour only)\n\n**Current Market Value**\n   - Price range for excellent condition (minimal wear, original headcover)\n   - Price range for good condition (normal play wear)\n   - Price range for project condition (significant wear, potential restoration candidate)\n   - Factors that affect this specific model's value\n\n **Buying Recommendations**\n   - Fair price benchmarks\n   - Specific condition issues to watch for with this model\n   - Restoration potential through Scotty Cameron Custom Shop\n   - use scotty cameron's thoughts on picking the right putter and write 50 words on why this putter may be right for the user.\n\n **Authentication Tips**\n   - Key markings and stampings to verify authenticity\n   - Common counterfeit indicators for this specific model\n   - Serial number location (if applicable)\n\n**Technical Specifications**\n   - Material composition (e.g., 303 stainless steel, GSS, carbon steel, Teryllium)\n   - Face technology (e.g., deep milled, dual-milled, insert type)\n   - Neck/hosel design (e.g., plumber's neck, flow neck, slant neck)\n   - Balance properties (face-balanced, toe hang)\n   - Weight technology (fixed, adjustable, customizable)\n   - Standard grip\n   - Distinctive cosmetic features\n\n **Collectibility Factors**\n   - Rarity\n   - Notable professional usage\n   - Special variations or releases\n   - Historical significance in Scotty Cameron lineup\n\n **Comparable Models**\n   - Similar Scotty Cameron models to consider as alternatives\n   - How this model compares to current lineup offerings\n\n#Pricing Advice\nEnsure all pricing information reflects current market conditions to the best of your ability. \n\n\n#General Knowledge to Inform Your Writing\n##Scotty Cameron's Thoughts on Picking the Right Putter for Your Game\nWhat's the most important factor in choosing the right putter?\nAfter you determine what you like aesthetically, and you've matched a design to your desired stroke style, getting the correct length is key. Because length affects your setup, which sets eye position, as well as another important specification: weight. These decisions all translate back to your stroke path, which will be directly related to your success rate in getting the ball in the cup. Get that length right for your game, and you're going to increase your odds for success. \n\nTell us more about how the length and weight should affect putter choice?\nLength is very important because it affects your entire setup, from eye position to posture to the putter's weight to the stroke path. If the putter shaft is too long, you stand back and the toe of the putter goes up in the air a bit. When that happens, your effective loft is aimed left and you're almost always going to pull putts. Too short, and you're crouched over. The eyes are outside of the target line and who knows where your putt is going? It's difficult to correct poor setup. Getting the length right for you so that the eyes remain about an inch inside the target line is what we've found to be the optimal setup. \n\nRegarding weight, we match the putter's length with a headweight that achieves a balanced swing weight. With our interchangeable sole weights, we can dial in the headweight to ensure that the putter doesn't feel either whippy or lethargic, but just right. \n\nHow are any of the above factors different when working with a Tour player?\nThey're not. Touring professionals also gravitate toward what they like to look at. It's usually where they start. Out on Tour, they may see a putter in our staff bag that appeals to them. Then, they take it out for a practice round and see how it goes. Many will also come to the Putter Studio for a fitting — or just a \"tune-up\" — to understand more about what they're trying to achieve with their putter and stroke. \n\nAll sorts of questions can be answered with the high-speed video data we gather when players come for a fitting. Is the setup working with the putter or against it? Where are the eyes positioned? What's the stroke path? We've been helping the best players in the world get a handle on the data associated with their strokes for a couple decades. It used to be a process reserved for the world's best players at my Putter Studio R&D facility. But, now with our Gallery open in Encinitas, anyone who's interested in a Tour-like fitting can schedule an appointment and come in to get fit like a pro. \n\nAre there any factors that most people don't think about that you'd suggest they explore when making a choice in putter?\nOne of the new ones I would suggest would be to examine your grip choice. What we have found on Tour and in the Putter Studio, is that these bigger grips on certain putters do work better for certain players. For example, the larger grips help to take a lot of the hands and feel out of the stroke. The larger grips help the player to make a stroke that's more of a shoulder turn, robotic and square-to-square. But, these larger grips on more flowing putters (heel and toe-weighted blades) don't seem to be the best match. They're fighting one another. So, we do put larger diameter Matador grips on Futura X and GOLO putters, but keep our smaller Pistolini and Pistolero options on the Select line. Grip choice has always been a factor in your putter setup. But, I think these days it's becoming a larger topic in the overall conversation about choosing the right putter.\n\n## Guide to Buying Used Scotty Cameron Putters\n## Most Desired Models\n- **Newport 2**: The most popular model, used by Tiger Woods to win 14 of his 15 major championships\n- **Del Mar**: Versatile mid-mallet design, newer versions include removable weights in the sole\n- **Phantom X**: Highly sought after due to tour pro usage (Justin Thomas uses a Phantom X 5, Patrick Cantlay uses a Phantom X 5.5)\n- **Vintage Models**: Original Teryllium putters from the mid-1990s and Pro Platinum models from the late 1990s\n\n## Where to Buy\n- **Online**: eBay (research seller ratings), Global Golf, 2nd Swing\n- **In-person**: Local golf retailers and pro shops (allows you to test the putter before purchase)\n\n## What to Look For - Wear and Condition\n- Scotty Camerons require extra care due to their soft materials\n- **Face condition**: Most important area to check—deep markings can affect putting consistency\n- **Teryllium models**: Check for rust if not oiled regularly\n- **Stainless steel models**: Look for dings and dents if headcover wasn't used\n- Always verify that the description matches the pictures\n- Ask for additional photos if anything is unclear\n\n## Customization Options\n- Scotty's Custom Shop can personalize your putter\n- Services range from simple paint fill and new grips to full restorations\n- Turnaround time: 3-4 months for full restorations\n- Cost: Up to $1,000 for complete customization\n\n## Red Flags and Deal-Breakers\n- Severe face defects\n- Signs of repairs, especially bonding issues\n- Counterfeit putters (particularly common with \"too good to be true\" pricing)\n- If uncertain about authenticity, ask for the serial number and verify with Titleist\n- Remember: If the price seems too good to be true, it probably is. Always authenticate your purchase if you have any doubts."
        
        # Try different approaches to set the system prompt depending on SDK version
        try:
            # Method 1: Try modern SDK approach
            message_params["system"] = system_prompt
        except:
            # If that fails, try the older approach
            try:
                message_params["system_prompt"] = system_prompt
            except:
                # If both fail, add it as a system message
                message_params["messages"].insert(0, {"role": "system", "content": system_prompt})
        
        # Make the API call with a direct try-except pattern
        try:
            # Check which client type we're using and patch accordingly
            client_class_name = client.__class__.__name__
            logger.info(f"Using client of type: {client_class_name}")
            
            # Depending on client type, we need to access messages.create differently
            if hasattr(client, 'messages') and hasattr(client.messages, 'create'):
                logger.info("Found messages.create method - applying patch")
                original_create = client.messages.create
                
                def patched_create(**kwargs):
                    # Log original parameters for debugging
                    logger.info(f"Original API call parameters: {list(kwargs.keys())}")
                    
                    # Filter out any potential problematic parameters
                    safe_kwargs = {k: v for k, v in kwargs.items() if k in [
                        "model", "max_tokens", "temperature", "messages", "system"
                    ]}
                    
                    logger.info(f"Making API call with safe parameters: {list(safe_kwargs.keys())}")
                    return original_create(**safe_kwargs)
                
                # Apply the patch
                client.messages.create = patched_create
                
                # Make the API call
                message = client.messages.create(**message_params)
            else:
                # For older client versions or direct completions API
                logger.warning("Could not find messages.create method, trying alternative approaches")
                
                # Try direct client.create call if it exists
                if hasattr(client, 'create'):
                    logger.info("Using client.create method")
                    message = client.create(**message_params)
                # If all else fails, try direct completion call
                elif hasattr(client, 'completions') and hasattr(client.completions, 'create'):
                    logger.info("Using completions.create method")
                    message = client.completions.create(**message_params)
                else:
                    raise Exception("No suitable method found to make API call")
            
            # Extract the text content from the response - handle potential structure changes
            try:
                # Try modern response structure first (messages API)
                if hasattr(message, 'content') and isinstance(message.content, list):
                    response_text = message.content[0].text
                # Try older response structures (completions API)
                elif hasattr(message, 'completion'):
                    response_text = message.completion
                elif hasattr(message, 'text'):
                    response_text = message.text
                else:
                    # Fallback to string representation
                    response_text = str(message)
                    
                logger.info("Successfully extracted response text")
            except (AttributeError, IndexError, TypeError) as e:
                logger.error(f"Error extracting response text: {str(e)}")
                # Fallback extraction method
                response_text = str(message.content if hasattr(message, 'content') else message)
            
            # Return the response
            return jsonify({"response": response_text})
            
        except Exception as api_error:
            logger.error(f"API call failed: {str(api_error)}")
            return jsonify({"error": f"API call failed: {str(api_error)}"}), 500
    
    except Exception as e:
        logger.error(f"Error in API call: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint for Railway"""
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    # Use environment variables with defaults
    port = int(os.environ.get('PORT', 8081))
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Log startup information
    logger.info(f"Starting Flask app on port {port} with debug={debug_mode}")
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=debug_mode) 