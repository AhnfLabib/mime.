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
        uri = crawler.settings.get("MONGODB_URI", "mongodb://localhost:27017")
        database = crawler.settings.get("MONGODB_DATABASE", "mime")
        collection = crawler.settings.get("MONGODB_COLLECTION", "creepypasta")
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
        # Upsert by URL to avoid duplicates
        self.collection.update_one(
            {"url": adapter.get("url")},
            {"$set": adapter.asdict(), "$setOnInsert": {"created_at": datetime.now(timezone.utc)}},
            upsert=True,
        )
        return item
