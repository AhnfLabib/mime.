# Q. - Creepypasta Scraper

A modern web application for scraping and browsing creepypasta stories from the Creepypasta Wiki.

## Features

- 🕷️ **Web Scraping**: Scrapes stories from [Creepypasta Wiki All Pages](https://creepypasta.fandom.com/wiki/Special:AllPages)
- 🎨 **Modern UI**: Black/white/red color scheme with responsive design
- 📊 **Real-time Progress**: Live progress tracking during scraping
- 🏷️ **Genre Classification**: Automatic genre detection and filtering
- 📱 **Responsive**: Works on desktop and mobile devices
- 💾 **Data Export**: JSONL output with optional MongoDB storage

## Quick Start

### 1. Install Dependencies
```bash
cd "/Users/ahnaflabib/Documents/Projects/mime."
source .venv/bin/activate
pip install -r requirements.txt  # If you create one
```

### 2. Run the Web Application
```bash
python app.py
```

### 3. Open in Browser
Navigate to: http://localhost:5000

### 4. Start Scraping
- Click the "Start Scraping" button
- Watch real-time progress
- Browse stories by genre
- Click stories to read full content

## Manual Scraping (Command Line)

```bash
# Scrape 50 stories
scrapy crawl creepypasta -s CLOSESPIDER_ITEMCOUNT=50 -s ROBOTSTXT_OBEY=False

# Scrape with MongoDB
scrapy crawl creepypasta -s MONGODB_ENABLED=True -s MONGODB_URI="mongodb://localhost:27017"
```

## Project Structure

```
mime./
├── app.py                          # Flask web application
├── mime_scraper/                   # Scrapy project
│   ├── items.py                    # Story data schema
│   ├── pipelines.py                # JSON & MongoDB pipelines
│   ├── middlewares.py              # User-agent rotation
│   ├── settings.py                 # Scrapy configuration
│   └── spiders/
│       └── creepypasta_spider.py  # Main scraping logic
├── templates/
│   └── index.html                  # Main web page
├── static/
│   ├── css/style.css              # Styling
│   └── js/app.js                  # Frontend JavaScript
├── outputs/                        # Scraped data (JSONL files)
└── scrapy.cfg                      # Scrapy configuration
```

## API Endpoints

- `GET /` - Main web interface
- `POST /api/start-scraping` - Start scraping process
- `GET /api/status` - Get scraping status
- `GET /api/stories` - Get all scraped stories
- `GET /api/stories/<genre>` - Get stories by genre

## Configuration

### Scrapy Settings
- **Rate Limiting**: 2-second delays between requests
- **User Agent Rotation**: Multiple browser user agents
- **AutoThrottle**: Enabled for respectful scraping
- **Output**: JSONL files in `outputs/` directory

### MongoDB (Optional)
Set in `mime_scraper/settings.py`:
```python
MONGODB_ENABLED = True
MONGODB_URI = "mongodb://localhost:27017"
MONGODB_DATABASE = "mime"
MONGODB_COLLECTION = "creepypasta"
```

## Genre Classification

Stories are automatically classified into genres based on tags:
- **Supernatural**: Ghosts, Demons, Monsters
- **Psychological**: Mental Illness, Dreams, Nightmares
- **Creature**: Vampires, Werewolves, Zombies
- **Sci-Fi**: Aliens, Technology, Space
- **Digital**: Internet, Video Games, Computers
- **Crime**: Serial Killers, Murder
- **Urban Legend**: Folklore, Mythology
- And more...

## Technology Stack

- **Backend**: Python, Flask, Scrapy
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Database**: MongoDB (optional)
- **Styling**: Custom CSS with Inter font
- **Icons**: Unicode emojis

## License

This project is for educational purposes. Please respect the Creepypasta Wiki's terms of service and robots.txt when scraping.

