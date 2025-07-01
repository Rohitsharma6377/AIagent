import os
import json
import random
import asyncio
from datetime import datetime, timedelta
try:
    from pytrends.request import TrendReq
except ImportError as e:
    print("pytrends is not installed. Please install it with 'pip install pytrends'.")
    raise e

CATEGORIES = {
    'SPORTS': 'all',
    'BUSINESS': 'b',
    'TECHNOLOGY': 't',
    'ENTERTAINMENT': 'e',
    'HEALTH': 'm',
    'SCIENCE': 's',
    'FUNNY': 'all',
    'MEMES': 'all',
}

FALLBACK_TOPICS = {
    'TECHNOLOGY': ['AI Breakthroughs', 'New Gadgets 2024', '5G Technology Explained'],
    'BUSINESS': ['Startup Success Stories', 'Investment Tips', 'Future of Work'],
    'SPORTS': ['Latest Cricket Highlights', 'Football Skills', 'Top 10 Athletes'],
    'ENTERTAINMENT': ['Best Movies of the Year', 'Celebrity News', 'New Music Releases'],
    'HEALTH': ['Mindfulness and Meditation', 'Healthy Eating Tips', 'At-Home Workouts'],
    'SCIENCE': ['Mind-blowing Science Facts', 'Mysteries of the Universe', 'Everyday Science Experiments'],
    'CULTURE': ['Incredible India', 'Indian Festivals', 'Traditional Indian Food'],
    'TRAVEL': ['Top 10 Places to Visit in India', 'Himalayan Adventures', 'Beaches of Goa'],
    'POLITICS': ['Indian Election Explained', 'New Government Policies', 'Indian Political History'],
    'ASTROLOGY': ['Daily Horoscope', 'Zodiac Sign Facts', 'Planetary Transits Explained'],
    'FUNNY': ['Latest Funny Memes', 'Stand Up Comedy Clips', 'Hilarious Animal Videos'],
    'MEMES': ['Latest Funny Memes', 'Dank Memes', 'Viral Memes'],
}

class TrendingTopicsFetcher:
    def __init__(self, region='IN'):
        self.region = region
        # Note: 'urllib3<2.0' is required for the current version of pytrends
        self.pytrends = TrendReq(hl='en-US', tz=330, retries=3, backoff_factor=0.5)

    def get_available_categories(self):
        """Returns a list of all available fallback categories."""
        return list(FALLBACK_TOPICS.keys())

    def get_topics(self, category_name=None):
        """
        Gets a list of trending topics. If the API fails, uses a fallback list.
        For 'FUNNY' or 'MEMES', fetches related trending meme queries.
        """
        try:
            if category_name and category_name.upper() in ['FUNNY', 'MEMES']:
                print(f"Fetching trending memes for {category_name}...")
                # Use suggestions or related_queries for meme-related keywords
                meme_keywords = ['memes', 'funny', 'viral memes', 'trending memes']
                all_memes = set()
                for kw in meme_keywords:
                    self.pytrends.build_payload([kw], cat=0, timeframe='now 7-d', geo=self.region)
                    related = self.pytrends.related_queries()
                    if kw in related and related[kw]['top'] is not None:
                        all_memes.update([q['query'] for q in related[kw]['top'].to_dict('records')])
                if all_memes:
                    return list(all_memes)
                # fallback to suggestions if no related queries
                suggestions = []
                for kw in meme_keywords:
                    try:
                        suggestions += [s['title'] for s in self.pytrends.suggestions(keyword=kw)]
                    except Exception:
                        continue
                if suggestions:
                    return suggestions
                print("No trending memes found, using fallback.")
            else:
                print(f"Fetching trends for {category_name or 'all categories'}...")
                df = self.pytrends.trending_searches(pn=self.region.lower())
                return df[0].tolist()
        except Exception as e:
            print(f"Error fetching trends: {e}. Using fallback topics.")
            if category_name and category_name in FALLBACK_TOPICS:
                return FALLBACK_TOPICS[category_name]
            all_fallback = []
            for topics in FALLBACK_TOPICS.values():
                all_fallback.extend(topics)
            return all_fallback

    def get_random_topic(self, category=None):
        trends = asyncio.run(self.get_topics(category))
        return random.choice(trends) if trends else None

if __name__ == "__main__":
    fetcher = TrendingTopicsFetcher(region='IN')
    
    print("\nFetching trends for all categories (will use fallback on error)...")
    all_trends = fetcher.get_topics()
    print(f"Sample topics: {all_trends[:5]}")
    
    print("\nGetting trending memes...")
    meme_topics = fetcher.get_topics('FUNNY')
    print(f"Sample meme topics: {meme_topics[:5]}")