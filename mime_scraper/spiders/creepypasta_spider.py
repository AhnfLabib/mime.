import re
from urllib.parse import urljoin

import scrapy
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

from mime_scraper.items import StoryItem


class CreepypastaSpider(scrapy.Spider):
    name = "creepypasta"
    allowed_domains = ["fandom.com", "creepypasta.fandom.com"]

    custom_settings = {
        # Ensure we respect target site
        "ROBOTSTXT_OBEY": True,
    }

    def __init__(self, start_urls=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Allow passing comma-separated start URLs via -a start_urls="url1,url2"
        if start_urls:
            self.start_urls = [u.strip() for u in start_urls.split(",") if u.strip()]
        else:
            # Default to All Pages to get all stories; user can override
            self.start_urls = [
                "https://creepypasta.fandom.com/wiki/Special:AllPages",
            ]

        # Optional: user agent pool used by middleware
        self.user_agent_pool = []

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = cls(*args, **kwargs)
        spider.crawler = crawler
        spider.settings = crawler.settings
        spider.user_agent_pool = crawler.settings.get("USER_AGENT_POOL", [])
        return spider

    def parse(self, response):
        # Find links to story pages from All Pages
        # All Pages uses '.mw-allpages-alphaindex a' for story links
        story_links = response.css(".mw-allpages-alphaindex a::attr(href)").getall()
        
        # Also check for direct story links in the main content
        story_links.extend(response.css("a[href*='/wiki/']:not([href*='Special:']):not([href*='Category:']):not([href*='File:']):not([href*='Template:']):not([href*='Help:']):not([href*='User:']):not([href*='Talk:']):not([href*='Forum:']):not([href*='Message_Wall:']):not([href*='Thread:']):not([href*='Topic:']):not([href*='Board:']):not([href*='Map:']):not([href*='Blog:']):not([href*='Module:']):not([href*='GeoJson:'])::attr(href)").getall())
        
        # Process story links
        for href in story_links:
            if href and not href.startswith('#'):
                url = response.urljoin(href)
                # Skip non-story pages more aggressively
                skip_patterns = [
                    'Special:', 'Category:', 'File:', 'Template:', 'Help:', 'User:', 'Talk:', 
                    'Forum:', 'Message_Wall:', 'Thread:', 'Topic:', 'Board:', 'Map:', 'Blog:', 
                    'Module:', 'GeoJson:', 'Community_Central', 'Creepypasta_Wiki', 'Main_Page',
                    'List_of_', 'Timeline', 'Gallery', 'Contest', 'Workshop', 'Rules', 'Policy'
                ]
                if any(skip in url for skip in skip_patterns):
                    continue
                yield scrapy.Request(url, callback=self.parse_story, errback=self.on_error)

        # Handle pagination: look for 'next' link in All Pages
        next_link = response.css("a.mw-nextlink::attr(href)").get()
        if next_link:
            yield response.follow(next_link, callback=self.parse, errback=self.on_error)

    def parse_story(self, response):
        item = StoryItem()
        item["url"] = response.url

        # Extract title from URL if not found in page
        url_title = response.url.split('/')[-1].replace('_', ' ')
        url_title = re.sub(r'\([^)]*\)', '', url_title).strip()  # Remove parentheses
        
        # Try multiple selectors for title
        title_selectors = [
            "h1.page-header__title::text",
            "h1#firstHeading::text", 
            "h1.mw-first-heading::text",
            ".page-header__title::text",
            "h1::text"
        ]
        
        title = None
        for selector in title_selectors:
            title = response.css(selector).get()
            if title and title.strip() and len(title.strip()) > 2:
                title = title.strip()
                break
        
        # Fallback to URL-based title if page title is generic or whitespace
        if not title or title.lower() in ['home', 'main page', 'untitled', 'creepypasta wiki'] or len(title.strip()) < 3:
            title = url_title or "Untitled"
        
        item["title"] = title

        # Extract author with multiple strategies
        author = None
        
        # Strategy 1: Look in infobox or metadata (be more specific)
        author_selectors = [
            ".portable-infobox .pi-data-label:contains('Author') + .pi-data-value *::text",
            ".portable-infobox .pi-data-label:contains('Writer') + .pi-data-value *::text"
        ]
        
        for selector in author_selectors:
            author = response.css(selector).get()
            if author and author.strip() and len(author.strip()) > 2:
                # Skip if it looks like a tag/category
                if not any(tag_word in author.lower() for tag_word in [
                    'category', 'tag', 'genre', 'type', 'archive', 'challenge', 
                    'nsfw', 'military', 'science', 'crime', 'mental', 'illness',
                    'dismemberment', 'weird', 'historical', 'plays', 'agb'
                ]):
                    author = author.strip()
                    break
        
        # Strategy 2: Look for "by AuthorName" patterns in content (only if we have actual story content)
        if not author:
            # Get content from the main story area, not metadata
            content_text = " ".join(response.css(".mw-parser-output p::text").getall()[:3])  # First 3 paragraphs only
            # Only try author extraction if we have substantial content
            if len(content_text.strip()) > 200:  # Only if we have real story content
                author_patterns = [
                    r"by\s+([A-Z][a-zA-Z\s\-\.']{2,30})",
                    r"Written by\s+([A-Z][a-zA-Z\s\-\.']{2,30})",
                    r"Author:\s*([A-Z][a-zA-Z\s\-\.']{2,30})",
                    r"Story by\s+([A-Z][a-zA-Z\s\-\.']{2,30})"
                ]
                
                for pattern in author_patterns:
                    match = re.search(pattern, content_text, re.IGNORECASE)
                    if match:
                        candidate = match.group(1).strip()
                        # Clean up common suffixes
                        candidate = re.sub(r'\s+(writes?|wrote|author|story).*$', '', candidate, flags=re.IGNORECASE)
                        # Skip if it looks like a tag/category or random text
                        if not any(tag_word in candidate.lower() for tag_word in [
                            'category', 'tag', 'genre', 'type', 'archive', 'challenge', 
                            'nsfw', 'military', 'science', 'crime', 'mental', 'illness',
                            'dismemberment', 'weird', 'historical', 'archive', 'plays', 'agb',
                            'horror', 'yig', 'shadowswimmer', 'digital', 'camera', 'crazed', 'lunatic',
                            'centimetres', 'goodwill', 'conceived', 'inch', 'find', 'nothing', 'usually',
                            'originally', 'upload', 'shinigami', 'eyes'
                        ]) and len(candidate) > 2 and len(candidate) < 50 and candidate.replace(' ', '').replace('-', '').replace('.', '').isalpha():
                            author = candidate
                            break
        
        # Strategy 3: Look for author at the end of content
        if not author:
            full_content = self.extract_raw_content(response)
            end_patterns = [
                r"Written by\s+([A-Z][a-zA-Z\s\-\.']{2,30})",
                r"by\s+([A-Z][a-zA-Z\s\-\.']{2,30})\s*$",
                r"Author:\s*([A-Z][a-zA-Z\s\-\.']{2,30})",
                r"Story by\s+([A-Z][a-zA-Z\s\-\.']{2,30})"
            ]
            
            for pattern in end_patterns:
                match = re.search(pattern, full_content[-500:], re.IGNORECASE)  # Last 500 chars
                if match:
                    candidate = match.group(1).strip()
                    candidate = re.sub(r'\s+(writes?|wrote|author|story).*$', '', candidate, flags=re.IGNORECASE)
                    # Skip if it looks like a tag/category
                    if not any(tag_word in candidate.lower() for tag_word in [
                        'category', 'tag', 'genre', 'type', 'archive', 'challenge', 
                        'nsfw', 'military', 'science', 'crime', 'mental', 'illness',
                        'dismemberment', 'weird', 'historical', 'archive', 'plays', 'agb',
                        'horror', 'yig', 'shadowswimmer'
                    ]) and len(candidate) > 2:
                        author = candidate
                        break
        
        item["author"] = author or "Unknown"

        # Publication date (if present in infobox or page metadata)
        pub_text = response.css(".portable-infobox .pi-data-label:contains('Date') + .pi-data-value *::text, .page-header__meta::text").get()
        publication_date = None
        if pub_text:
            try:
                publication_date = dateparser.parse(pub_text, fuzzy=True).date().isoformat()
            except Exception:
                publication_date = None
        item["publication_date"] = publication_date

        # Tags (categories)
        tags = response.css("#articleCategories a.category::text, a[rel='tag']::text, .page-header__categories a::text").getall()
        tags = [t.strip() for t in tags if t and t.strip()]
        item["tags"] = list(dict.fromkeys(tags)) if tags else []

        # Content: main article body with improved cleaning
        html = response.css(".mw-parser-output").get() or response.text
        cleaned = self.clean_content(html, author)
        item["content"] = cleaned

        yield item

    def extract_raw_content(self, response):
        """Extract raw content for author detection at the end"""
        html = response.css(".mw-parser-output").get() or response.text
        soup = BeautifulSoup(html, "lxml")
        
        # Remove unwanted elements
        for el in soup.select("script, style, .reference, .mw-editsection"):
            el.decompose()
        
        return soup.get_text(" ", strip=True)

    def clean_content(self, html: str, author: str = None) -> str:
        soup = BeautifulSoup(html, "lxml")
        
        # Remove only the most obvious non-content elements
        selectors_to_remove = [
            "script",
            "style",
            ".mw-editsection",
            ".printfooter",
            ".catlinks",
            ".mw-category-group",
            ".mw-normal-catlinks"
        ]
        
        for sel in selectors_to_remove:
            for el in soup.select(sel):
                el.decompose()

        # Extract content from the main parser output area
        content_area = soup.select_one(".mw-parser-output")
        if not content_area:
            return ""
        
        # Get all text content from paragraphs and divs
        text_parts = []
        for element in content_area.find_all(["p", "div", "ul", "ol"]):
            # Skip if it's a navigation element
            if element.get("class") and any(cls in ["navbox", "toc", "catlinks"] for cls in element.get("class", [])):
                continue
                
            text = element.get_text(" ", strip=True)
            if text and len(text) > 10:  # Only skip very short text
                # Skip only obvious navigation content
                if not any(skip in text.lower() for skip in [
                    'category:', 'categories:', 'navigation', 'menu', 'sidebar',
                    'advertisement', 'ad', 'sponsor', 'related articles',
                    'see also', 'external links', 'references', 'jump to',
                    'retrieved from', 'this page was last edited', 'content is available under',
                    'jump to navigation', 'search'
                ]):
                    text_parts.append(text)
        
        # Join and clean up
        text = "\n\n".join(text_parts)
        
        # Remove author attribution at the end if we found it
        if author and author != "Unknown":
            # Remove patterns like "Written by AuthorName" at the end
            text = re.sub(rf'\s*(Written by|by|Author:)\s+{re.escape(author)}.*$', '', text, flags=re.IGNORECASE)
        
        # Remove common footer patterns
        footer_patterns = [
            r'Content is available under.*$',
            r'This page was last edited.*$',
            r'Categories:.*$',
            r'Retrieved from.*$',
            r'Jump to.*$'
        ]
        
        for pattern in footer_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'(\n\s*)+', '\n\n', text)
        
        return text.strip()

    def on_error(self, failure):
        req = failure.request
        self.logger.warning(f"Request failed: {req.url} - {failure.getErrorMessage()}")
        # Skip after logging; Scrapy retry middleware will handle transient errors

