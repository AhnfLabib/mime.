# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from datetime import datetime, timezone


class StoryItem(scrapy.Item):
    # Basic story information
    title = scrapy.Field()
    author = scrapy.Field()
    content = scrapy.Field()
    publication_date = scrapy.Field()
    tags = scrapy.Field()
    url = scrapy.Field()
    
    # Enhanced metadata for AI training
    genre_primary = scrapy.Field()  # Main genre classification
    genre_secondary = scrapy.Field()  # Secondary genre tags
    writing_style = scrapy.Field()  # Analysis metrics (word count, avg sentence length, complexity)
    tropes = scrapy.Field()  # Detected story tropes (e.g., "unreliable narrator", "twist ending")
    content_metadata = scrapy.Field()  # Word density, unique word ratio, readability score
    scraped_at = scrapy.Field()  # Timestamp when scraped
    updated_at = scrapy.Field()  # Timestamp when last updated
