# Putter Trader - Scotty Cameron Putter Information App

A simple web application that allows users to get detailed information about Scotty Cameron putters by leveraging Anthropic's Claude AI model.

## Features

- Input a Scotty Cameron putter model name
- Get comprehensive details about the putter including:
  - Basic information (year, model family, etc.)
  - Current market value
  - Technical specifications
  - Authentication tips
  - Collectibility factors
  - And more!

## Setup

1. Clone this repository
2. Create a `.env` file with your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the application:
   ```
   python app.py
   ```
5. Open your browser and navigate to `http://localhost:5000`

## Technologies Used

- Flask (Python web framework)
- Anthropic API (Claude 3.7 Sonnet)
- HTML/CSS/JavaScript 