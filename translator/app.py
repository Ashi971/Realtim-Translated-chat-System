import os
import asyncio
import threading
import speech_recognition as sr
from deep_translator import GoogleTranslator, exceptions
import edge_tts
import pygame
import io
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*", logger=True)

# Configuration
LANG_VOICES = {
    "en": {"male": "en-US-GuyNeural", "female": "en-US-JennyNeural"},
    "ml": {"male": "ml-IN-MidhunNeural", "female": "ml-IN-SobhanaNeural"},
    "hi": {"male": "hi-IN-MadhurNeural", "female": "hi-IN-SwaraNeural"},
}

SUPPORTED_LANGUAGES = {
    "en": "English",
    "ml": "Malayalam",
    "hi": "Hindi",
    "es": "Spanish",
    "fr": "French",
}

# Global state
rooms = {}
recognizer = sr.Recognizer()
pygame.mixer.init()

@app.context_processor
def inject_globals():
    return {'SUPPORTED_LANGUAGES': SUPPORTED_LANGUAGES}

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/server')
def server():
    server_lang = request.args.get('server_lang')
    client_lang = request.args.get('client_lang')
    room_id = request.args.get('room_id', '').strip() or os.urandom(4).hex()
    
    if not validate_language(server_lang) or not validate_language(client_lang):
        return "Invalid language code", 400
    
    rooms[room_id] = {
        'server_lang': server_lang,
        'client_lang': client_lang,
        'server_sid': None,
        'client_sid': None
    }
    
    return render_template('server.html',
                         server_lang=server_lang,
                         client_lang=client_lang,
                         room_id=room_id)

@app.route('/client')
def client():
    room_id = request.args.get('room_id')
    if room_id not in rooms:
        return "Room not found", 404
    
    return render_template('client.html',
                         server_lang=rooms[room_id]['server_lang'],
                         client_lang=rooms[room_id]['client_lang'],
                         room_id=room_id)

# Socket.IO Handlers
@socketio.on('connect')
def handle_connect():
    print(f"New connection: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    for room_id, room_data in rooms.items():
        if room_data['server_sid'] == request.sid:
            room_data['server_sid'] = None
            emit('server_disconnected', room=room_id)
        elif room_data['client_sid'] == request.sid:
            room_data['client_sid'] = None
            emit('client_disconnected', room=room_id)

@socketio.on('join_room')
def handle_join_room(data):
    room_id = data['room_id']
    role = data['role']
    
    if room_id not in rooms:
        emit('error', {'message': 'Invalid room ID'})
        return
    
    join_room(room_id)
    
    if role == 'server':
        rooms[room_id]['server_sid'] = request.sid
        emit('server_ready', {'room_id': room_id})
    elif role == 'client':
        rooms[room_id]['client_sid'] = request.sid
        emit('client_ready', {'room_id': room_id})
    
    if rooms[room_id]['server_sid'] and rooms[room_id]['client_sid']:
        emit('connection_established', {'room_id': room_id}, room=room_id)

@socketio.on('send_message')
def handle_message(data):
    room_id = data['room_id']
    if room_id not in rooms:
        return
    
    room = rooms[room_id]
    sender = data['sender']
    text = data['text']
    
    if sender == 'server':
        translated = translate(text, room['server_lang'], room['client_lang'])
        emit('receive_message', {
            'text': translated,
            'original': text,
            'sender': 'server'
        }, room=room['client_sid'])
    else:
        translated = translate(text, room['client_lang'], room['server_lang'])
        emit('receive_message', {
            'text': translated,
            'original': text,
            'sender': 'client'
        }, room=room['server_sid'])

# Helper functions
def validate_language(code):
    return code in SUPPORTED_LANGUAGES

def translate(text, src, dest):
    try:
        return GoogleTranslator(source=src, target=dest).translate(text)
    except Exception as e:
        print(f"Translation error: {e}")
        return text

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)