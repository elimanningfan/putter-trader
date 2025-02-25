import os
from flask import Flask, render_template, request, jsonify
import anthropic
from dotenv import load_dotenv
import logging
import sys
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
        
        # Ensure we're not passing any unsupported parameters (like 'proxies')
        # Check the installed version and only pass supported parameters
        anthropic_version = getattr(anthropic, "__version__", "0.0.0")
        
        # Initialize with just the API key to avoid any compatibility issues
        # This works across all Anthropic SDK versions
        try:
            # Explicitly use only the api_key parameter to avoid any injected parameters from middleware
            client_kwargs = {"api_key": api_key}
            # Explicitly construct the client with only the api_key parameter
            client = anthropic.Anthropic(**client_kwargs)
            logger.info("Anthropic client initialized successfully")
        except TypeError as te:
            # If there's a TypeError about unexpected keyword arguments, log and re-raise
            logger.error(f"TypeError initializing client: {str(te)}")
            # Just try the most basic initialization possible
            client = anthropic.Anthropic(api_key=api_key)
            logger.info("Fallback client initialization successful")
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
            # Create message parameters with only the known required parameters
            # to avoid any compatibility issues with different SDK versions
            message = None
            try:
                # First try the standard method
                message = client.messages.create(**message_params)
            except TypeError as te:
                # If we get a TypeError about unexpected arguments
                logger.warning(f"Encountered TypeError in API call: {str(te)}")
                # Filter out any problematic parameters that might be causing issues
                # Keep only the essential parameters that work across different SDK versions
                essential_params = {
                    "model": message_params["model"],
                    "max_tokens": message_params["max_tokens"],
                    "messages": message_params["messages"]
                }
                if "temperature" in message_params:
                    essential_params["temperature"] = message_params["temperature"]
                if "system" in message_params:
                    essential_params["system"] = message_params["system"]
                
                logger.info("Retrying API call with essential parameters only")
                message = client.messages.create(**essential_params)
            
            # Extract the text content from the response - handle potential structure changes
            try:
                response_text = message.content[0].text
                logger.info("Successfully extracted response text")
            except (AttributeError, IndexError, TypeError) as e:
                logger.error(f"Error extracting response text: {str(e)}")
                # Fallback extraction method
                response_text = str(message.content)
            
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