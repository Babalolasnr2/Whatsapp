from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
# Enable CORS for all origins, which is often necessary for SocketIO testing
CORS(app, resources={r"/*": {"origins": "*"}}) 

# Use a non-default secret key
app.config['SECRET_KEY'] = 'your_secret_key_here' 

# Initialize SocketIO with a message queue if you use async workers (optional)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- State Management ---
# Key: 'room_id' (e.g., 'chat_room'), Value: Set of active SIDs (session IDs)
online_users = {}
ROOM_ID = 'main_chat_room' # Simplicity for a 2-person chat

# --- Routes ---

@app.route('/')
def index():
    """Renders the main chat page."""
    return render_template('index.html')

# --- SocketIO Event Handlers ---

@socketio.on('connect')
def handle_connect():
    """Handles a new client connection."""
    user_sid = request.sid
    join_room(ROOM_ID)
    
    # Track the user as online
    if ROOM_ID not in online_users:
        online_users[ROOM_ID] = set()
    online_users[ROOM_ID].add(user_sid)
    
    print(f"User {user_sid} connected and joined room {ROOM_ID}")
    
    # Notify everyone in the room about the updated online count
    update_online_status()

@socketio.on('disconnect')
def handle_disconnect():
    """Handles a client disconnecting."""
    user_sid = request.sid
    if ROOM_ID in online_users and user_sid in online_users[ROOM_ID]:
        online_users[ROOM_ID].remove(user_sid)
    
    print(f"User {user_sid} disconnected from room {ROOM_ID}")
    
    leave_room(ROOM_ID)
    
    # Notify everyone in the room about the updated online count
    update_online_status()

@socketio.on('send_message')
def handle_message(data):
    """Handles incoming chat messages from a client."""
    
    # 1. Prepare Message Data
    sender_id = request.sid
    message_text = data['message']
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Determine read/delivery status based on the current number of online users
    online_count = len(online_users.get(ROOM_ID, set()))
    
    # 1 mark (delivered) if online_count is 1 (only sender)
    # 2 marks (read/seen) if online_count is 2 (sender + recipient)
    status_marks = 1 if online_count == 1 else 2
    
    # 2. Compile Final Message Data
    final_message = {
        'sender_id': sender_id,
        'text': message_text,
        'time': timestamp,
        'status': status_marks,
        # A simple way to differentiate sender/recipient on the client
        'is_me': request.sid == sender_id 
    }

    # 3. Broadcast the message to all clients in the room
    # 'include_self=True' means the sender also receives their own message
    emit('receive_message', final_message, room=ROOM_ID)
    
    # Update the status marks for all messages
    if status_marks == 2:
        # If the count is 2, it means the other user just came online
        # We should tell the client to update any *previous* 1-mark messages to 2-marks
        # Note: A real app would track this in a database. Here we just trigger a status update.
        socketio.emit('update_read_status', {'status': 2}, room=ROOM_ID)


def update_online_status():
    """Emits the current online count to all clients."""
    online_count = len(online_users.get(ROOM_ID, set()))
    
    # Indicate to the client if the recipient is online (online_count == 2)
    recipient_is_online = online_count == 2
    
    emit('status_update', 
         {'online_count': online_count, 
          'recipient_online': recipient_is_online}, 
         room=ROOM_ID, 
         include_self=True)

if __name__ == '__main__':
    # Use '0.0.0.0' for external access if needed, otherwise '127.0.0.1'
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    
