<!-- d1ec2445-6e0c-4cb0-a098-9d9a0a1d1d60 c0753563-ea98-42a8-a410-0e42ec146c47 -->
# MongoDB Atlas Integration Plan

## Overview

Transform the creepypasta scraper to use MongoDB Atlas as the primary data source with enhanced categorization for AI training purposes.

## Phase 1: MongoDB Atlas Setup & Configuration

### 1.1 Create MongoDB Atlas Account (Manual Steps - Detailed Guide)

**You will need to:**

1. Go to https://www.mongodb.com/cloud/atlas/register
2. Sign up with email or Google account (free tier available)
3. Create a new cluster:

   - Choose "M0 Sandbox" (Free tier)
   - Select cloud provider (AWS recommended)
   - Choose region closest to you
   - Name your cluster (e.g., "creepypasta-cluster")

4. Wait 3-5 minutes for cluster creation
5. Create database user:

   - Click "Database Access" in left sidebar
   - Click "Add New Database User"
   - Choose "Password" authentication
   - Username: `mime_user` (or your choice)
   - Generate strong password and SAVE IT
   - Select "Read and write to any database"

6. Configure network access:

   - Click "Network Access" in left sidebar
   - Click "Add IP Address"
   - Click "Allow Access from Anywhere" (0.0.0.0/0)
   - Confirm

7. Get connection string:

   - Click "Database" in left sidebar
   - Click "Connect" on your cluster
   - Choose "Connect your application"
   - Copy the connection string (looks like: `mongodb+srv://username:<password>@cluster.xxxxx.mongodb.net/`)
   - Replace `<password>` with your actual password

### 1.2 Install MongoDB Python Driver

**File: `requirements.txt`** (create if doesn't exist)

```txt
pymongo[srv]>=4.6.0
dnspython>=2.4.0
```

### 1.3 Create Environment Configuration

**File: `.env`** (new file at project root)

```
MONGODB_URI=mongodb+srv://mime_user:YOUR_PASSWORD@cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=mime
MONGODB_COLLECTION=creepypasta_stories
```

### 1.4 Update Settings

**File: `mime_scraper/settings.py`**

- Change `MONGODB_ENABLED = False` to `MONGODB_ENABLED = True`
- Update MongoDB settings to read from environment variables
- Add genre classification fields

## Phase 2: Enhanced Data Model for AI Training

### 2.1 Create Story Schema with AI Training Metadata

**File: `mime_scraper/items.py`**

Add new fields:

- `genre_primary`: Main genre classification
- `genre_secondary`: Secondary genre tags
- `writing_style`: Analysis metrics (word count, avg sentence length, complexity)
- `tropes`: Detected story tropes (e.g., "unreliable narrator", "twist ending")
- `content_metadata`: Word density, unique word ratio, readability score
- `scraped_at`: Timestamp
- `updated_at`: Timestamp

### 2.2 Create Advanced Genre Classifier

**File: `mime_scraper/classifiers.py`** (new)

Implement multi-level classification:

- Primary genres: Supernatural, Psychological, Creature, Crime, Sci-Fi, Urban Legend
- Secondary tags: Body horror, Found footage, Ritual, Technology
- Story tropes: Twist ending, Unreliable narrator, Meta, Reality distortion
- Writing style metrics: Calculate word density, sentence complexity, vocabulary richness

### 2.3 Update Pipeline for Enhanced Storage

**File: `mime_scraper/pipelines.py`**

Enhance `MongoPipeline`:

- Add genre classification before storage
- Calculate writing style metrics
- Add indexes on: genre, tags, scraped_at
- Store complete metadata for AI training

## Phase 3: Flask API MongoDB Integration

### 3.1 Create MongoDB Connection Manager

**File: `app.py`**

Replace JSONL reading with MongoDB queries:

- Add MongoDB client initialization
- Create database helper functions
- Implement connection pooling
- Add error handling for database operations

### 3.2 Update API Endpoints

**File: `app.py`**

Modify endpoints to query MongoDB:

- `/api/stories` - Query all stories with pagination
- `/api/stories/<genre>` - Filter by primary genre
- `/api/stories/search` - Search by tags, tropes, or content
- `/api/stats` - Get genre distribution and writing style stats
- `/api/export` - Export filtered data for AI training

### 3.3 Add New Endpoints for AI Training

**File: `app.py`**

New endpoints:

- `/api/training-data` - Get stories formatted for model training
- `/api/style-analysis/<story_id>` - Get detailed writing style metrics
- `/api/tropes` - Get all detected tropes with frequencies

## Phase 4: Data Migration

### 4.1 Create Migration Script

**File: `scripts/migrate_to_mongodb.py`** (new)

Script to:

1. Connect to MongoDB Atlas
2. Read all JSONL files from `outputs/` directory
3. Process each story through genre classifier
4. Calculate writing style metrics
5. Upload to MongoDB with proper schema
6. Show progress bar and summary
7. Verify data integrity

### 4.2 Backup Current Data

Before migration:

- Create backup directory
- Copy all JSONL files to backup location

## Phase 5: Frontend Updates

### 5.1 Update API Calls

**File: `static/js/app.js`**

- Update to handle MongoDB response format
- Add pagination controls
- Add advanced filtering (by tropes, writing style)
- Display writing style metrics on story cards

### 5.2 Add AI Training Data Export UI

**File: `templates/index.html`**

Add new section:

- Button to export filtered stories for training
- Display writing style statistics
- Show trope distribution charts

## Implementation Files

### Key Files to Modify:

1. `mime_scraper/settings.py` - MongoDB config
2. `mime_scraper/items.py` - Enhanced schema
3. `mime_scraper/pipelines.py` - Enhanced storage
4. `mime_scraper/classifiers.py` - NEW: Genre & style classification
5. `app.py` - MongoDB integration
6. `scripts/migrate_to_mongodb.py` - NEW: Migration script
7. `static/js/app.js` - API updates
8. `.env` - NEW: Environment config
9. `requirements.txt` - Add dependencies

### Database Indexes (Created by migration script):

```javascript
db.creepypasta_stories.createIndex({ "url": 1 }, { unique: true })
db.creepypasta_stories.createIndex({ "genre_primary": 1 })
db.creepypasta_stories.createIndex({ "tags": 1 })
db.creepypasta_stories.createIndex({ "tropes": 1 })
db.creepypasta_stories.createIndex({ "scraped_at": -1 })
```

## Detailed Step-by-Step Execution Guide

**I will guide you through each step with:**

1. Exact commands to run
2. What to expect at each step
3. How to verify it worked
4. What to do if there are errors
5. Screenshots/examples of MongoDB Atlas UI

**After you set up MongoDB Atlas and provide the connection string, I will:**

1. Install required packages
2. Create all necessary files
3. Run the migration script with progress updates
4. Test all endpoints
5. Verify data in MongoDB Atlas (I'll show you how)
6. Update the frontend

## Success Criteria

- ✅ MongoDB Atlas cluster operational
- ✅ All existing stories migrated with enhanced metadata
- ✅ Scrapy spider stores directly to MongoDB
- ✅ Flask API reads from MongoDB with <100ms response time
- ✅ Genre classification accuracy >90%
- ✅ Writing style metrics calculated for all stories
- ✅ Frontend displays enhanced categorization
- ✅ Export endpoint ready for AI training data

### To-dos

- [ ] Set up MongoDB Atlas account and cluster (manual step with detailed guide)
- [ ] Install pymongo and dnspython packages
- [ ] Create .env file with MongoDB connection string
- [ ] Add AI training fields to items.py (genre, tropes, writing_style)
- [ ] Create classifiers.py with genre and style analysis
- [ ] Enhance MongoPipeline with classification and metadata
- [ ] Enable MongoDB in settings.py and add environment variable support
- [ ] Create migration script to import existing JSONL data
- [ ] Update Flask app to use MongoDB as primary data source
- [ ] Add new API endpoints for AI training data export
- [ ] Update JavaScript to handle MongoDB data format and new features
- [ ] Execute migration script to import all existing stories
- [ ] Test all endpoints and verify data in MongoDB Atlas