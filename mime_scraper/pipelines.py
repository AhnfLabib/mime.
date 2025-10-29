# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from datetime import datetime, timezone
import json
import os
from typing import Optional

from pymongo import MongoClient
from .classifiers import classify_story
from .llm_cleaner import clean_story_with_gemini

class JsonLinesPipeline:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file = None

    @classmethod
    def from_crawler(cls, crawler):
        output_dir = crawler.settings.get("JSON_OUTPUT_DIR", "outputs")
        os.makedirs(output_dir, exist_ok=True)
        now = datetime.now(timezone.utc)
        file_path = os.path.join(output_dir, f"creepypasta_{now.strftime('%Y%m%d_%H%M%S')}.jsonl")
        return cls(file_path=file_path)

    def open_spider(self, spider):
        self.file = open(self.file_path, "w", encoding="utf-8")

    def close_spider(self, spider):
        if self.file:
            self.file.close()

    def process_item(self, item, _spider):
        adapter = ItemAdapter(item)
        line = json.dumps(adapter.asdict(), ensure_ascii=False)
        self.file.write(line + "\n")
        return item


class LLMCleaningPipeline:
    def __init__(self, enabled: bool):
        self.enabled = enabled

    @classmethod
    def from_crawler(cls, crawler):
        return cls(enabled=crawler.settings.getbool("LLM_CLEANING_ENABLED", False))

    def process_item(self, item, _spider):
        if not self.enabled:
            return item
        adapter = ItemAdapter(item)
        cleaned = clean_story_with_gemini(adapter.asdict())
        for key, value in cleaned.items():
            adapter[key] = value
        return item


class MongoPipeline:
    def __init__(self, uri: str, database: str, collection: str):
        self.mongo_uri = uri
        self.mongo_db = database
        self.collection_name = collection
        self.client: Optional[MongoClient] = None
        self.collection = None

    @classmethod
    def from_crawler(cls, crawler):
        if not crawler.settings.getbool("MONGODB_ENABLED", False):
            return None
        
        # Try to get MongoDB URI from environment variable first
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        uri = os.getenv("MONGODB_URI") or crawler.settings.get("MONGODB_URI", "mongodb://localhost:27017")
        database = os.getenv("MONGODB_DATABASE") or crawler.settings.get("MONGODB_DATABASE", "mime")
        collection = os.getenv("MONGODB_COLLECTION") or crawler.settings.get("MONGODB_COLLECTION", "creepypasta_stories")
        return cls(uri=uri, database=database, collection=collection)

    def open_spider(self, spider):
        if self.mongo_uri:
            self.client = MongoClient(self.mongo_uri)
            self.collection = self.client[self.mongo_db][self.collection_name]

    def close_spider(self, spider):
        if self.client:
            self.client.close()

    def process_item(self, item, _spider):
        if not self.collection:
            return item
        
        adapter = ItemAdapter(item)
        
        # Get basic story data
        title = adapter.get("title", "")
        content = adapter.get("content", "")
        tags = adapter.get("tags", [])
        
        # Classify story and get enhanced metadata
        classification = classify_story(title, content, tags)
        
        # Add enhanced metadata to item
        adapter["genre_primary"] = classification["genre_primary"]
        adapter["genre_secondary"] = classification["genre_secondary"]
        adapter["tropes"] = classification["tropes"]
        adapter["writing_style"] = classification["writing_style"]
        adapter["scraped_at"] = datetime.now(timezone.utc)
        adapter["updated_at"] = datetime.now(timezone.utc)
        
        # Prepare document for MongoDB
        doc = adapter.asdict()
        
        # Upsert by URL to avoid duplicates
        self.collection.update_one(
            {"url": doc["url"]},
            {
                "$set": doc,
                "$setOnInsert": {"created_at": datetime.now(timezone.utc)}
            },
            upsert=True,
        )
        
        return item
