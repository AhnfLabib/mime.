# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class StoryItem(scrapy.Item):
    title = scrapy.Field()
    author = scrapy.Field()
    content = scrapy.Field()
    publication_date = scrapy.Field()
    tags = scrapy.Field()
    url = scrapy.Field()
