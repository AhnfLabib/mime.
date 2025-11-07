import os
import json
import subprocess
import threading
import time
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from collections import defaultdict
from pymongo import MongoClient
from dotenv import load_dotenv
try:
    import google.generativeai as genai
except Exception:
    genai = None

app = Flask(__name__)
CORS(app)

# Load environment variables
load_dotenv()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
if genai is not None and os.getenv("GEMINI_API_KEY"):
    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    except Exception:
        pass

# MongoDB connection
mongodb_client = None
mongodb_db = None
mongodb_collection = None

def get_mongodb_connection():
    """Get MongoDB connection"""
    global mongodb_client, mongodb_db, mongodb_collection
    
    if mongodb_client is None:
        try:
            mongodb_uri = os.getenv("MONGODB_URI")
            if not mongodb_uri or "YOUR_PASSWORD" in mongodb_uri:
                raise Exception("MongoDB URI not configured properly")
            
            mongodb_client = MongoClient(mongodb_uri)
            mongodb_db = mongodb_client[os.getenv("MONGODB_DATABASE", "mime")]
            mongodb_collection = mongodb_db[os.getenv("MONGODB_COLLECTION", "creepypasta_stories")]
            
            # Test connection
            mongodb_client.admin.command('ping')
            print("✅ Connected to MongoDB Atlas")
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            mongodb_client = None
            mongodb_db = None
            mongodb_collection = None
    
    return mongodb_client, mongodb_db, mongodb_collection

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

# Store scraping logs
scraping_logs = []
MAX_LOG_LINES = 1000  # Keep last 1000 lines

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
        
        # Clear previous logs
        scraping_logs.clear()
        scraping_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Starting spider...")
        
        process = subprocess.Popen(
            cmd,
            cwd=project_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Combine stderr into stdout
            text=True,
            bufsize=1,  # Line buffered
            env={**os.environ, "PATH": f"{project_dir}/.venv/bin:{os.environ.get('PATH', '')}"}
        )
        
        # Monitor progress and capture logs in real-time
        def read_output(proc):
            """Read output from process in real-time"""
            while True:
                output = proc.stdout.readline()
                if output == '' and proc.poll() is not None:
                    break
                if output:
                    line = output.strip()
                    if line:
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        log_entry = f"[{timestamp}] {line}"
                        scraping_logs.append(log_entry)
                        # Keep only last MAX_LOG_LINES
                        if len(scraping_logs) > MAX_LOG_LINES:
                            scraping_logs.pop(0)
                        print(log_entry)  # Also print to server console
        
        # Start log reader thread
        log_thread = threading.Thread(target=read_output, args=(process,))
        log_thread.daemon = True
        log_thread.start()
        
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
        
        # Wait for log thread to finish
        log_thread.join(timeout=5)
        
        # Read any remaining output
        remaining = process.stdout.read()
        if remaining:
            for line in remaining.strip().split('\n'):
                if line.strip():
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    scraping_logs.append(f"[{timestamp}] {line.strip()}")
                    if len(scraping_logs) > MAX_LOG_LINES:
                        scraping_logs.pop(0)
        
        scraping_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Spider process completed.")
        
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

@app.route('/api/logs')
def get_logs():
    """Get scraping logs"""
    return jsonify({
        'logs': scraping_logs,
        'total_lines': len(scraping_logs),
        'is_running': scraping_status['is_running']
    })

@app.route('/api/stories')
def get_stories():
    """Get all scraped stories from MongoDB"""
    try:
        client, db, collection = get_mongodb_connection()
        if collection is None:
            return jsonify({'error': 'MongoDB not available'}), 500
        
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        skip = (page - 1) * per_page
        
        # Get stories with pagination
        stories = list(collection.find().skip(skip).limit(per_page).sort('scraped_at', -1))
        
        # Convert ObjectId to string for JSON serialization
        for story in stories:
            story['_id'] = str(story['_id'])
        
        # Get total count
        total = collection.count_documents({})
        
        # Get genre statistics
        pipeline = [
            {"$group": {"_id": "$genre_primary", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        genre_stats = list(collection.aggregate(pipeline))
        genres = {stat['_id']: stat['count'] for stat in genre_stats}
        
        return jsonify({
            'stories': stories,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
            'genres': genres
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stories/<genre>')
def get_stories_by_genre(genre):
    """Get stories filtered by genre from MongoDB"""
    try:
        client, db, collection = get_mongodb_connection()
        if collection is None:
            return jsonify({'error': 'MongoDB not available'}), 500
        
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        skip = (page - 1) * per_page
        
        # Get stories filtered by genre
        stories = list(collection.find({"genre_primary": genre}).skip(skip).limit(per_page).sort('scraped_at', -1))
        
        # Convert ObjectId to string for JSON serialization
        for story in stories:
            story['_id'] = str(story['_id'])
        
        # Get total count for this genre
        total = collection.count_documents({"genre_primary": genre})
        
        return jsonify({
            'stories': stories,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
            'genre': genre
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/training-data')
def get_training_data():
    """Get stories formatted for AI model training"""
    try:
        client, db, collection = get_mongodb_connection()
        if collection is None:
            return jsonify({'error': 'MongoDB not available'}), 500
        
        # Get filter parameters
        genre = request.args.get('genre')
        min_word_count = int(request.args.get('min_word_count', 100))
        max_word_count = int(request.args.get('max_word_count', 10000))
        
        # Build query
        query = {
            "writing_style.word_count": {"$gte": min_word_count, "$lte": max_word_count}
        }
        if genre:
            query["genre_primary"] = genre
        
        # Get stories
        stories = list(collection.find(query).sort('scraped_at', -1))
        
        # Format for training
        training_data = []
        for story in stories:
            training_data.append({
                'id': str(story['_id']),
                'title': story.get('title', ''),
                'content': story.get('content', ''),
                'genre_primary': story.get('genre_primary', ''),
                'genre_secondary': story.get('genre_secondary', []),
                'tropes': story.get('tropes', []),
                'writing_style': story.get('writing_style', {}),
                'tags': story.get('tags', [])
            })
        
        return jsonify({
            'training_data': training_data,
            'total': len(training_data),
            'filters': {
                'genre': genre,
                'min_word_count': min_word_count,
                'max_word_count': max_word_count
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """Get comprehensive statistics about the story collection"""
    try:
        client, db, collection = get_mongodb_connection()
        if collection is None:
            return jsonify({'error': 'MongoDB not available'}), 500
        
        # Basic stats
        total_stories = collection.count_documents({})
        
        # Genre distribution
        genre_pipeline = [
            {"$group": {"_id": "$genre_primary", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        genre_stats = list(collection.aggregate(genre_pipeline))
        
        # Trope distribution (guard for missing/empty arrays)
        trope_pipeline = [
            {"$match": {"tropes": {"$exists": True, "$type": "array", "$ne": []}}},
            {"$unwind": "$tropes"},
            {"$group": {"_id": "$tropes", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        trope_stats = list(collection.aggregate(trope_pipeline))
        
        # Writing style stats
        style_pipeline = [
            {"$group": {
                "_id": None,
                "avg_word_count": {"$avg": "$writing_style.word_count"},
                "avg_sentence_length": {"$avg": "$writing_style.avg_sentence_length"},
                "avg_readability": {"$avg": "$writing_style.readability_score"},
                "min_word_count": {"$min": "$writing_style.word_count"},
                "max_word_count": {"$max": "$writing_style.word_count"}
            }}
        ]
        style_stats = list(collection.aggregate(style_pipeline))
        
        return jsonify({
            'total_stories': total_stories,
            'genre_distribution': {stat['_id']: stat['count'] for stat in genre_stats},
            'trope_distribution': {stat['_id']: stat['count'] for stat in trope_stats},
            'writing_style_stats': style_stats[0] if style_stats else {},
            'last_updated': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tropes')
def get_tropes():
    """Get all detected tropes with frequencies"""
    try:
        client, db, collection = get_mongodb_connection()
        if collection is None:
            return jsonify({'error': 'MongoDB not available'}), 500
        
        pipeline = [
            {"$unwind": "$tropes"},
            {"$group": {"_id": "$tropes", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        trope_stats = list(collection.aggregate(pipeline))
        
        return jsonify({
            'tropes': {stat['_id']: stat['count'] for stat in trope_stats},
            'total_unique_tropes': len(trope_stats)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate', methods=['POST'])
def generate_story():
    """Generate a new story using Gemini, conditioned on genre/tropes/style."""
    try:
        if not os.getenv("GEMINI_API_KEY"):
            return jsonify({'error': 'GEMINI_API_KEY not configured'}), 400
        if genai is None:
            return jsonify({'error': 'google-generativeai not installed'}), 400

        body = request.get_json(force=True) or {}
        genre = body.get('genre', 'Uncategorized')
        tropes = body.get('tropes', [])
        style = body.get('style', {})
        seed_titles = int(body.get('seed_titles', 0))

        seeds = []
        # Try to get seeds from MongoDB, but don't fail if unavailable
        if seed_titles > 0:
            try:
                client, db, collection = get_mongodb_connection()
                if collection is not None:
                    q = {"genre_primary": genre}
                    if tropes:
                        q["tropes"] = {"$in": tropes}
                    seeds = list(collection.find(q, {"title": 1, "content": 1}).sort('scraped_at', -1).limit(seed_titles))
            except Exception as mongo_err:
                print(f"MongoDB unavailable for seeds: {mongo_err}")
                # Continue without seeds

        sys_inst = "You write original creepypasta stories. Do not copy any provided text. Output plain text only."
        constraints = f"Target genre: {genre}. Tropes: {', '.join(tropes)}. Aim style: {style}."
        seed_excerpt = "\n\n".join([f"EXAMPLE: {s.get('title','')} — {s.get('content','')[:600]}" for s in seeds])

        prompt = f"{constraints}\n\nInspiration excerpts (do not copy):\n{seed_excerpt}\n\nNow write a new, original story (~{style.get('word_count', 1000)} words)."

        # Try working models - using official SDK naming (without models/ prefix)
        candidate_models = [GEMINI_MODEL, "gemini-2.5-flash", "gemini-2.0-flash"]
        last_err = None
        text = ""
        for m in candidate_models:
            try:
                model = genai.GenerativeModel(m, system_instruction=sys_inst)
                resp = model.generate_content(prompt)
                text = (resp.text or '').strip()
                if text:
                    break
            except Exception as e:
                last_err = e
                continue
        if not text and last_err:
            return jsonify({'error': str(last_err)}), 400
        return jsonify({
            'story': text,
            'used_seeds': [s.get('title','') for s in seeds]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", "5000"))
    app.run(debug=True, host='0.0.0.0', port=port)

