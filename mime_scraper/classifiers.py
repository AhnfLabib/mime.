"""
Advanced genre and style classification for creepypasta stories
"""

import re
import math
from typing import List, Dict, Tuple, Any
from collections import Counter


class GenreClassifier:
    """Classify stories into genres and detect tropes"""
    
    def __init__(self):
        # Primary genre mapping
        self.primary_genres = {
            'Supernatural': ['ghost', 'spirit', 'demon', 'devil', 'supernatural', 'paranormal', 'haunted', 'possession'],
            'Psychological': ['mental', 'insanity', 'psychosis', 'hallucination', 'delusion', 'trauma', 'nightmare', 'dream'],
            'Creature': ['monster', 'alien', 'zombie', 'vampire', 'werewolf', 'beast', 'creature', 'entity'],
            'Crime': ['murder', 'killer', 'serial', 'death', 'crime', 'police', 'investigation', 'evidence'],
            'Sci-Fi': ['technology', 'computer', 'internet', 'digital', 'future', 'experiment', 'scientific', 'ai'],
            'Urban Legend': ['legend', 'myth', 'folklore', 'urban', 'rumor', 'story', 'tale', 'hearsay']
        }
        
        # Secondary tags
        self.secondary_tags = {
            'Body Horror': ['dismemberment', 'gore', 'blood', 'mutilation', 'disfigurement'],
            'Found Footage': ['footage', 'video', 'recording', 'camera', 'tape', 'documentary'],
            'Ritual': ['ritual', 'ceremony', 'sacrifice', 'cult', 'worship', 'summoning'],
            'Technology': ['computer', 'internet', 'digital', 'online', 'software', 'hardware'],
            'Military': ['military', 'soldier', 'war', 'combat', 'base', 'operation'],
            'Medical': ['hospital', 'doctor', 'patient', 'medical', 'surgery', 'treatment']
        }
        
        # Story tropes
        self.tropes = {
            'Twist Ending': ['twist', 'surprise', 'unexpected', 'reveal', 'shock'],
            'Unreliable Narrator': ['unreliable', 'untrustworthy', 'questionable', 'doubtful'],
            'Meta': ['meta', 'self-aware', 'fourth wall', 'breaking', 'awareness'],
            'Reality Distortion': ['reality', 'dimension', 'parallel', 'alternate', 'universe'],
            'Time Loop': ['loop', 'repeat', 'cycle', 'recurring', 'replay'],
            'Isolation': ['alone', 'isolated', 'trapped', 'stranded', 'cut off'],
            'Childhood Trauma': ['child', 'kid', 'young', 'innocent', 'vulnerable'],
            'Technology Gone Wrong': ['malfunction', 'glitch', 'error', 'bug', 'failure']
        }
    
    def classify_genre(self, title: str, content: str, tags: List[str]) -> Tuple[str, List[str]]:
        """Classify story into primary genre and secondary tags"""
        text = f"{title} {content}".lower()
        tag_text = " ".join(tags).lower()
        combined_text = f"{text} {tag_text}"
        
        # Score primary genres
        genre_scores = {}
        for genre, keywords in self.primary_genres.items():
            score = sum(1 for keyword in keywords if keyword in combined_text)
            genre_scores[genre] = score
        
        # Get primary genre (highest score, default to 'Uncategorized')
        primary_genre = max(genre_scores, key=genre_scores.get) if max(genre_scores.values()) > 0 else 'Uncategorized'
        
        # Get secondary tags
        secondary_tags = []
        for tag, keywords in self.secondary_tags.items():
            if any(keyword in combined_text for keyword in keywords):
                secondary_tags.append(tag)
        
        return primary_genre, secondary_tags
    
    def detect_tropes(self, content: str) -> List[str]:
        """Detect story tropes in content"""
        content_lower = content.lower()
        detected_tropes = []
        
        for trope, keywords in self.tropes.items():
            if any(keyword in content_lower for keyword in keywords):
                detected_tropes.append(trope)
        
        return detected_tropes


class WritingStyleAnalyzer:
    """Analyze writing style metrics for AI training"""
    
    def analyze(self, content: str) -> Dict[str, Any]:
        """Analyze writing style and return metrics"""
        if not content or len(content.strip()) == 0:
            return self._empty_metrics()
        
        # Basic text statistics
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        word_count = len(words)
        sentence_count = len(sentences)
        
        if word_count == 0 or sentence_count == 0:
            return self._empty_metrics()
        
        # Calculate metrics
        avg_sentence_length = word_count / sentence_count
        avg_word_length = sum(len(word) for word in words) / word_count
        
        # Vocabulary richness
        unique_words = set(word.lower() for word in words)
        vocabulary_richness = len(unique_words) / word_count
        
        # Word frequency analysis
        word_freq = Counter(word.lower() for word in words)
        most_common_words = dict(word_freq.most_common(10))
        
        # Readability approximation (simplified Flesch Reading Ease)
        # Higher score = easier to read
        readability_score = self._calculate_readability(avg_sentence_length, avg_word_length)
        
        # Complexity indicators
        complex_words = [word for word in words if len(word) > 6]
        complexity_ratio = len(complex_words) / word_count
        
        # Dialogue analysis
        dialogue_indicators = ['"', "'", 'said', 'asked', 'replied', 'whispered', 'shouted']
        dialogue_count = sum(1 for word in words if word.lower() in dialogue_indicators)
        dialogue_ratio = dialogue_count / word_count
        
        return {
            'word_count': word_count,
            'sentence_count': sentence_count,
            'avg_sentence_length': round(avg_sentence_length, 2),
            'avg_word_length': round(avg_word_length, 2),
            'vocabulary_richness': round(vocabulary_richness, 3),
            'readability_score': round(readability_score, 2),
            'complexity_ratio': round(complexity_ratio, 3),
            'dialogue_ratio': round(dialogue_ratio, 3),
            'most_common_words': most_common_words,
            'unique_word_count': len(unique_words)
        }
    
    def _calculate_readability(self, avg_sentence_length: float, avg_word_length: float) -> float:
        """Calculate simplified readability score"""
        # Simplified Flesch Reading Ease formula
        # 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_word_length)
        score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_word_length)
        return max(0, min(100, score))  # Clamp between 0 and 100
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics for empty content"""
        return {
            'word_count': 0,
            'sentence_count': 0,
            'avg_sentence_length': 0,
            'avg_word_length': 0,
            'vocabulary_richness': 0,
            'readability_score': 0,
            'complexity_ratio': 0,
            'dialogue_ratio': 0,
            'most_common_words': {},
            'unique_word_count': 0
        }


def classify_story(title: str, content: str, tags: List[str]) -> Dict[str, Any]:
    """Main function to classify a story and return all metadata"""
    genre_classifier = GenreClassifier()
    style_analyzer = WritingStyleAnalyzer()
    
    # Get genre classification
    primary_genre, secondary_tags = genre_classifier.classify_genre(title, content, tags)
    
    # Detect tropes
    tropes = genre_classifier.detect_tropes(content)
    
    # Analyze writing style
    writing_style = style_analyzer.analyze(content)
    
    return {
        'genre_primary': primary_genre,
        'genre_secondary': secondary_tags,
        'tropes': tropes,
        'writing_style': writing_style
    }
