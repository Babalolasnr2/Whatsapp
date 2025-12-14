from flask import Flask, request, jsonify
from flask_cors import CORS
import time

# --- Setup ---
app = Flask(__name__)
# Enable CORS for development so the HTML file can talk to the server
CORS(app)

# A simple list to store the chat messages
# In a real application, this would be a database.
chat_messages = []
# Tracks the ID for new messages
message_id_counter = 1

# --- API Endpoints ---

@app.route('/api/messages', methods=['GET'])
def get_messages():
    """Returns the current list of chat messages."""
    # We return the entire list for simplicity, but in a production app, 
    # we would only return new messages (polling).
    return jsonify(chat_messages)

@app.route('/api/send', methods=['POST'])
def send_message():
    """Receives a new message and adds it to the list."""
    global message_id_counter
    
    # Get the JSON data sent from the JavaScript frontend
    data = request.json
    
    if not data or 'username' not in data or 'text' not in data:
        return jsonify({'error': 'Missing username or text'}), 400

    # Create the new message object
    new_message = {
        'id': message_id_counter,
        'username': data['username'],
        'text': data['text'],
        'timestamp': time.strftime('%H:%M:%S', time.localtime())
    }

    # Add the message to our global list
    chat_messages.append(new_message)
    message_id_counter += 1
    
    # Return success confirmation
    return jsonify({'status': 'Message received', 'message_id': new_message['id']}), 201

# --- Run Server ---

if __name__ == '__main__':
    print("Starting Flask server...")
    print("API is available at http://127.0.0.1:5000")
    print("Open index.html in your browser.")
    # Run the app on port 5000
    app.run(debug=True, port=5000)



