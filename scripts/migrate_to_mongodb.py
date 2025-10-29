#!/usr/bin/env python3
"""
Migration script to import existing JSONL data to MongoDB Atlas
"""

import os
import sys
import json
import glob
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pymongo import MongoClient
from dotenv import load_dotenv
from mime_scraper.classifiers import classify_story


def load_environment():
    """Load environment variables"""
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        print("❌ .env file not found. Please create it with your MongoDB Atlas connection string.")
        return False
    
    # Check if MongoDB URI is configured
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri or "YOUR_PASSWORD" in mongodb_uri:
        print("❌ MongoDB URI not properly configured in .env file.")
        print("Please update the MONGODB_URI with your actual MongoDB Atlas connection string.")
        return False
    
    return True


def connect_to_mongodb() -> MongoClient:
    """Connect to MongoDB Atlas"""
    try:
        mongodb_uri = os.getenv("MONGODB_URI")
        client = MongoClient(mongodb_uri)
        
        # Test connection
        client.admin.command('ping')
        print("✅ Connected to MongoDB Atlas successfully!")
        return client
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB Atlas: {e}")
        sys.exit(1)


def get_jsonl_files() -> List[str]:
    """Get all JSONL files from outputs directory"""
    outputs_dir = project_root / "outputs"
    if not outputs_dir.exists():
        print("❌ Outputs directory not found.")
        return []
    
    jsonl_files = glob.glob(str(outputs_dir / "*.jsonl"))
    if not jsonl_files:
        print("❌ No JSONL files found in outputs directory.")
        return []
    
    print(f"📁 Found {len(jsonl_files)} JSONL files to migrate")
    return jsonl_files


def process_story(story_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single story with classification and metadata"""
    # Get basic data
    title = story_data.get("title", "")
    content = story_data.get("content", "")
    tags = story_data.get("tags", [])
    
    # Classify story
    classification = classify_story(title, content, tags)
    
    # Add enhanced metadata
    story_data["genre_primary"] = classification["genre_primary"]
    story_data["genre_secondary"] = classification["genre_secondary"]
    story_data["tropes"] = classification["tropes"]
    story_data["writing_style"] = classification["writing_style"]
    story_data["scraped_at"] = datetime.now(timezone.utc)
    story_data["updated_at"] = datetime.now(timezone.utc)
    
    return story_data


def create_indexes(collection):
    """Create database indexes for better performance"""
    print("🔧 Creating database indexes...")
    
    indexes = [
        ("url", 1),  # Unique index on URL
        ("genre_primary", 1),  # Index on primary genre
        ("tags", 1),  # Index on tags
        ("tropes", 1),  # Index on tropes
        ("scraped_at", -1),  # Index on scraped date (descending)
        ("writing_style.word_count", 1),  # Index on word count
    ]
    
    for field, direction in indexes:
        try:
            if field == "url":
                collection.create_index([(field, direction)], unique=True)
            else:
                collection.create_index([(field, direction)])
            print(f"  ✅ Created index on {field}")
        except Exception as e:
            print(f"  ⚠️  Index on {field} already exists or failed: {e}")


def migrate_data():
    """Main migration function"""
    print("🚀 Starting MongoDB migration...")
    
    # Load environment
    if not load_environment():
        return False
    
    # Connect to MongoDB
    client = connect_to_mongodb()
    
    # Get database and collection
    database_name = os.getenv("MONGODB_DATABASE", "mime")
    collection_name = os.getenv("MONGODB_COLLECTION", "creepypasta_stories")
    
    db = client[database_name]
    collection = db[collection_name]
    
    print(f"📊 Using database: {database_name}, collection: {collection_name}")
    
    # Get JSONL files
    jsonl_files = get_jsonl_files()
    if not jsonl_files:
        return False
    
    # Create backup directory
    backup_dir = project_root / "backup"
    backup_dir.mkdir(exist_ok=True)
    print(f"📦 Backup directory: {backup_dir}")
    
    # Process each file
    total_stories = 0
    processed_stories = 0
    errors = 0
    
    for file_path in jsonl_files:
        print(f"\n📄 Processing file: {os.path.basename(file_path)}")
        
        # Backup original file
        backup_file = backup_dir / os.path.basename(file_path)
        with open(file_path, 'r', encoding='utf-8') as src, open(backup_file, 'w', encoding='utf-8') as dst:
            dst.write(src.read())
        
        # Read and process stories
        stories = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    try:
                        story_data = json.loads(line)
                        processed_story = process_story(story_data)
                        stories.append(processed_story)
                        total_stories += 1
                    except json.JSONDecodeError as e:
                        print(f"  ⚠️  Error parsing line {line_num}: {e}")
                        errors += 1
                        continue
        
        # Insert stories into MongoDB
        if stories:
            print(f"  📝 Inserting {len(stories)} stories...")
            
            # Use upsert to avoid duplicates
            for story in tqdm(stories, desc="  Processing"):
                try:
                    collection.update_one(
                        {"url": story["url"]},
                        {"$set": story, "$setOnInsert": {"created_at": datetime.now(timezone.utc)}},
                        upsert=True
                    )
                    processed_stories += 1
                except Exception as e:
                    print(f"    ❌ Error inserting story {story.get('title', 'Unknown')}: {e}")
                    errors += 1
    
    # Create indexes
    create_indexes(collection)
    
    # Print summary
    print(f"\n📊 Migration Summary:")
    print(f"  📁 Files processed: {len(jsonl_files)}")
    print(f"  📖 Total stories found: {total_stories}")
    print(f"  ✅ Successfully processed: {processed_stories}")
    print(f"  ❌ Errors: {errors}")
    print(f"  📦 Backups created in: {backup_dir}")
    
    # Verify data in MongoDB
    total_in_db = collection.count_documents({})
    print(f"  🗄️  Total stories in MongoDB: {total_in_db}")
    
    # Show genre distribution
    print(f"\n📈 Genre Distribution:")
    pipeline = [
        {"$group": {"_id": "$genre_primary", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    genre_stats = list(collection.aggregate(pipeline))
    for stat in genre_stats:
        print(f"  {stat['_id']}: {stat['count']} stories")
    
    client.close()
    print("\n🎉 Migration completed successfully!")
    return True


if __name__ == "__main__":
    try:
        migrate_data()
    except KeyboardInterrupt:
        print("\n⚠️  Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
