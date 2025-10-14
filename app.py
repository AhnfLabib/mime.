import os
import json
import subprocess
import threading
import time
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from collections import defaultdict

app = Flask(__name__)
CORS(app)

# Global variables for tracking scraping status
scraping_status = {
    'is_running': False,
    'progress': 0,
    'total_items': 0,
    'current_item': 0,
    'start_time': None,
    'end_time': None,
    'error': None
}

scraped_stories = []
genre_stats = defaultdict(int)

def classify_genre(tags):
    """Classify story into main genre based on tags"""
    if not tags:
        return "Uncategorized"
    
    # Genre mapping based on common creepypasta tags
    genre_mapping = {
        'Ghosts': 'Supernatural',
        'Mental Illness': 'Psychological',
        'Demons': 'Supernatural',
        'Devil': 'Supernatural',
        'Monsters': 'Creature',
        'Aliens': 'Sci-Fi',
        'Zombies': 'Creature',
        'Vampires': 'Creature',
        'Werewolves': 'Creature',
        'Serial Killers': 'Crime',
        'Murder': 'Crime',
        'Death': 'Dark',
        'Horror': 'Horror',
        'Nightmare': 'Psychological',
        'Dreams': 'Psychological',
        'Sleep': 'Psychological',
        'Halloween': 'Seasonal',
        'Christmas': 'Seasonal',
        'Technology': 'Sci-Fi',
        'Internet': 'Digital',
        'Video Games': 'Digital',
        'Computers': 'Digital',
        'Urban Legend': 'Urban Legend',
        'Folklore': 'Urban Legend',
        'Mythology': 'Urban Legend'
    }
    
    # Check tags for genre classification
    for tag in tags:
        for keyword, genre in genre_mapping.items():
            if keyword.lower() in tag.lower():
                return genre
    
    # Default classification based on first tag
    return tags[0] if tags else "Uncategorized"

def run_spider():
    """Run the Scrapy spider in a separate thread"""
    global scraping_status, scraped_stories, genre_stats
    
    try:
        scraping_status['is_running'] = True
        scraping_status['start_time'] = datetime.now().isoformat()
        scraping_status['error'] = None
        scraping_status['progress'] = 0
        
        # Change to project directory and run spider
        project_dir = "/Users/ahnaflabib/Documents/Projects/mime."
        cmd = [
            "python", "-m", "scrapy", "crawl", "creepypasta",
            "-s", "CLOSESPIDER_ITEMCOUNT=50",
            "-s", "ROBOTSTXT_OBEY=False",
            "-L", "INFO"
        ]
        
        process = subprocess.Popen(
            cmd,
            cwd=project_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={**os.environ, "PATH": f"{project_dir}/.venv/bin:{os.environ.get('PATH', '')}"}
        )
        
        # Monitor progress
        while process.poll() is None:
            time.sleep(2)
            # Check for new output files
            output_dir = os.path.join(project_dir, "outputs")
            if os.path.exists(output_dir):
                jsonl_files = [f for f in os.listdir(output_dir) if f.endswith('.jsonl')]
                if jsonl_files:
                    latest_file = max(jsonl_files, key=lambda x: os.path.getctime(os.path.join(output_dir, x)))
                    file_path = os.path.join(output_dir, latest_file)
                    
                    # Count items in file
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        current_count = len([line for line in lines if line.strip()])
                        scraping_status['current_item'] = current_count
                        scraping_status['total_items'] = 50  # Target
                        scraping_status['progress'] = min((current_count / 50) * 100, 100)
        
        # Load scraped data
        output_dir = os.path.join(project_dir, "outputs")
        if os.path.exists(output_dir):
            jsonl_files = [f for f in os.listdir(output_dir) if f.endswith('.jsonl')]
            if jsonl_files:
                latest_file = max(jsonl_files, key=lambda x: os.path.getctime(os.path.join(output_dir, x)))
                file_path = os.path.join(output_dir, latest_file)
                
                scraped_stories = []
                genre_stats = defaultdict(int)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            story = json.loads(line)
                            # Classify genre
                            story['genre'] = classify_genre(story.get('tags', []))
                            genre_stats[story['genre']] += 1
                            scraped_stories.append(story)
        
        scraping_status['end_time'] = datetime.now().isoformat()
        scraping_status['is_running'] = False
        
    except Exception as e:
        scraping_status['error'] = str(e)
        scraping_status['is_running'] = False
        scraping_status['end_time'] = datetime.now().isoformat()

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/start-scraping', methods=['POST'])
def start_scraping():
    """Start the scraping process"""
    global scraping_status
    
    if scraping_status['is_running']:
        return jsonify({'error': 'Scraping is already running'}), 400
    
    # Start scraping in a separate thread
    thread = threading.Thread(target=run_spider)
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Scraping started'})

@app.route('/api/status')
def get_status():
    """Get current scraping status"""
    return jsonify(scraping_status)

@app.route('/api/stories')
def get_stories():
    """Get all scraped stories"""
    return jsonify({
        'stories': scraped_stories,
        'total': len(scraped_stories),
        'genres': dict(genre_stats)
    })

@app.route('/api/stories/<genre>')
def get_stories_by_genre(genre):
    """Get stories filtered by genre"""
    filtered_stories = [story for story in scraped_stories if story.get('genre') == genre]
    return jsonify({
        'stories': filtered_stories,
        'total': len(filtered_stories),
        'genre': genre
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

