from flask import Flask, render_template, request, session, redirect, url_for
import re
import os
from textblob import TextBlob 

app = Flask(__name__)
# IMPORTANT: Set a secret key for secure session management (required for history feature)
app.secret_key = os.urandom(24) 

# Emotion Keywords, Emojis, and Colors (6 Core Emotions)
emotion_data = {
    'Happy': {'keywords': ['joy', 'happy', 'great', 'awesome', 'good', 'love', 'amazing', 'fun', 'superb', 'excited'], 'emoji': '😊', 'color': '#28a745'}, 
    'Sad': {'keywords': ['sad', 'bad', 'worst', 'unhappy', 'cry', 'difficult', 'stress', 'low', 'depressed', 'gloomy', 'disappointed'], 'emoji': '😢', 'color': '#dc3545'}, 
    'Angry': {'keywords': ['angry', 'mad', 'hate', 'stupid', 'fight', 'annoyed', 'terrible', 'frustrated', 'rage', 'furious'], 'emoji': '😠', 'color': '#ffc107'}, 
    'Surprise': {'keywords': ['wow', 'surprise', 'unbelievable', 'shocking', 'unexpected', 'oh my god', 'unforeseen', 'suddenly'], 'emoji': '😲', 'color': '#17a2b8'}, 
    'Fear': {'keywords': ['fear', 'scary', 'afraid', 'terrifying', 'danger', 'horrible', 'anxiety', 'panic', 'nervous', 'worried'], 'emoji': '😨', 'color': '#6f42c1'},
    'Disgust': {'keywords': ['disgust', 'gross', 'ugly', 'nasty', 'awful', 'vomit', 'yuck', 'repulsive', 'sickening'], 'emoji': '🤢', 'color': '#795548'} 
}
NEUTRAL_EMOTION = 'Neutral'

# --- Text Preprocessing Function (Includes Spelling Correction) ---
def preprocess_text(text):
    """
    Converts text to lowercase, corrects spelling using TextBlob, and tokenizes.
    """
    text = text.lower()
    
    # Spelling Correction: Key professional feature to handle typos like 'exited' -> 'excited'
    try:
        corrected_text = str(TextBlob(text).correct())
    except Exception:
        corrected_text = text # Fallback
    
    # Tokenization: Extracts individual words
    return re.findall(r'\b\w+\b', corrected_text) 

# --- Emotion Detection Core Function ---
def detect_emotion_with_scores(text):
    words = preprocess_text(text) 
    
    emotion_scores = {emotion: 0 for emotion in emotion_data}
    
    # Calculate scores based on keyword matches
    for word in words:
        for emotion, data in emotion_data.items():
            if word in data['keywords']:
                emotion_scores[emotion] += 1
                
    max_score = 0
    detected_emotion = NEUTRAL_EMOTION
    
    # Determine the winning emotion
    for emotion, score in emotion_scores.items():
        if score > max_score:
            max_score = score
            detected_emotion = emotion
        elif score == max_score and score > 0 and detected_emotion != NEUTRAL_EMOTION:
             detected_emotion = 'Mixed'
    
    if max_score == 0:
        detected_emotion = NEUTRAL_EMOTION
        
    # Prepare final result (with emoji) and data for the chart
    if detected_emotion == 'Mixed':
        final_result = "Mixed / Ambiguous 🤔"
        result_color = '#6c757d' # Gray
    elif detected_emotion == NEUTRAL_EMOTION:
        final_result = f"{NEUTRAL_EMOTION} 😐"
        result_color = '#6c757d' 
    else:
        final_result = f"{detected_emotion} {emotion_data[detected_emotion]['emoji']}"
        result_color = emotion_data[detected_emotion]['color']

    # Data for Chart.js
    chart_labels = list(emotion_scores.keys())
    chart_data = list(emotion_scores.values())
    chart_colors = [emotion_data[e]['color'] for e in chart_labels]

    return final_result, chart_labels, chart_data, chart_colors, result_color, emotion_scores

# --- Flask Web App Routes ---

@app.route('/')
def home():
    if 'history' not in session:
        session['history'] = []
    
    # Reverse history for newest entry first
    history_reversed = list(reversed(session['history']))
    
    # FIX: Initialize all chart variables to empty lists for the home page load
    return render_template('index.html', 
                           history=history_reversed,
                           chart_labels=[],
                           chart_data=[],
                           chart_colors=[])

@app.route('/predict', methods=['POST'])
def predict():
    if request.method == 'POST':
        text = request.form['text_input']
        
        final_result, labels, data, colors, result_color, scores_raw = detect_emotion_with_scores(text)
        
        # Add to history
        entry = {
            'text': text,
            'result': final_result,
            'score': scores_raw,
            'color': result_color
        }
        session['history'].append(entry)
        session.modified = True
        
        # Pass all data to the template
        return render_template('index.html', 
                               result_text=text, 
                               prediction=final_result,
                               chart_labels=labels,
                               chart_data=data,
                               chart_colors=colors,
                               result_color=result_color,
                               history=list(reversed(session['history'])))

@app.route('/clear_history')
def clear_history():
    session.pop('history', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)