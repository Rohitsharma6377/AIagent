import os
import json
import random
import asyncio
from datetime import datetime, timedelta
from pytrends.request import TrendReq

CATEGORIES = {
    'SPORTS': 'all',
    'BUSINESS': 'b',
    'TECHNOLOGY': 't',
    'ENTERTAINMENT': 'e',
    'HEALTH': 'm',
    'SCIENCE': 's'
}

FALLBACK_TOPICS = {
    'SPORTS': ['Latest Cricket Highlights', 'Football Skills', 'Top 10 Athletes'],
    'BUSINESS': ['Startup Success Stories', 'Investment Tips', 'Future of Work'],
    'TECHNOLOGY': ['AI Breakthroughs', 'New Gadgets 2024', '5G Technology Explained'],
    'ENTERTAINMENT': ['Best Movies of the Year', 'Celebrity News', 'New Music Releases'],
    'HEALTH': ['Mindfulness and Meditation', 'Healthy Eating Tips', 'At-Home Workouts'],
    'SCIENCE': ['Space Discoveries', 'Climate Change Solutions', 'The Human Brain']
}

class TrendingTopicsFetcher:
    def __init__(self, region='IN'):
        self.region = region
        # Note: 'urllib3<2.0' is required for the current version of pytrends
        self.pytrends = TrendReq(hl='en-US', tz=330, retries=3, backoff_factor=0.5)

    def get_topics(self, category_name=None):
        """
        Gets a list of trending topics. If the API fails, uses a fallback list.
        """
        try:
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
    
    print("\nGetting topics for Technology...")
    tech_topics = fetcher.get_topics('TECHNOLOGY')
    print(f"Sample tech topics: {tech_topics[:3]}")