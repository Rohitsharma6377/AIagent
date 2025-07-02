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
    'TECHNOLOGY': [
        'AI Breakthroughs', 'New Gadgets 2024', '5G Technology Explained',
        'Quantum Computing Basics', 'How Blockchain Works', 'The Future of Robotics',
        'SpaceX Starship Updates', 'Virtual Reality in 2024', 'Top Programming Languages',
        'Cybersecurity Tips', 'Smart Home Innovations', 'Wearable Tech Trends'
    ],
    'BUSINESS': [
        'Startup Success Stories', 'Investment Tips', 'Future of Work',
        'How to Start a Business', 'Stock Market Basics', 'Entrepreneurship in India',
        'Remote Work Trends', 'Personal Finance Hacks', 'Women in Business',
        'Marketing Strategies', 'E-commerce Growth', 'Sustainable Businesses'
    ],
    'SPORTS': [
        'Latest Cricket Highlights', 'Football Skills', 'Top 10 Athletes',
        'Olympic Records', 'Famous Indian Sports Moments', 'How to Improve Stamina',
        'Yoga for Athletes', 'Best Sports Movies', 'Women in Sports',
        'Sports Nutrition', 'Motivational Sports Stories', 'Upcoming Tournaments'
    ],
    'ENTERTAINMENT': [
        'Best Movies of the Year', 'Celebrity News', 'New Music Releases',
        'Bollywood vs Hollywood', 'Top Web Series', 'Movie Review: Latest Blockbuster',
        'Behind the Scenes: Film Making', 'Music Trends 2024', 'Stand-up Comedy',
        'Dance Challenges', 'Viral Entertainment Videos', 'Award Show Highlights'
    ],
    'HEALTH': [
        'Mindfulness and Meditation', 'Healthy Eating Tips', 'At-Home Workouts',
        'Mental Health Awareness', 'Yoga for Beginners', 'Superfoods Explained',
        'How to Sleep Better', 'Fitness Myths Busted', 'Immunity Boosting Tips',
        'Healthy Habits for Kids', 'Stress Management', 'Benefits of Walking'
    ],
    'SCIENCE': [
        'Mind-blowing Science Facts', 'Mysteries of the Universe', 'Everyday Science Experiments',
        'Space Exploration', 'Famous Scientists', 'How Vaccines Work',
        'Climate Change Explained', 'Physics in Daily Life', 'The Human Brain',
        'Genetics Basics', 'Renewable Energy', 'Cool Chemistry Tricks'
    ],
    'CULTURE': [
        'Incredible India', 'Indian Festivals', 'Traditional Indian Food',
        'Folk Dances of India', 'Indian Mythology', 'Cultural Diversity',
        'Art and Craft Traditions', 'Famous Indian Monuments', 'Indian Languages',
        'History of Yoga', 'Indian Literature', 'Bollywood Culture'
    ],
    'TRAVEL': [
        'Top 10 Places to Visit in India', 'Himalayan Adventures', 'Beaches of Goa',
        'Backpacking Tips', 'Wildlife Sanctuaries', 'Travel on a Budget',
        'Hidden Gems of India', 'Road Trips', 'Travel Safety Tips',
        'Cultural Etiquette', 'Best Street Food', 'Eco-friendly Travel'
    ],
    'POLITICS': [
        'Indian Election Explained', 'New Government Policies', 'Indian Political History',
        'Women in Politics', 'Youth and Politics', 'Famous Political Leaders',
        'How Laws are Made', 'Political Debates', 'Role of Media in Politics',
        'Constitution of India', 'Voting Rights', 'Recent Political Events'
    ],
    'ASTROLOGY': [
        'Daily Horoscope', 'Zodiac Sign Facts', 'Planetary Transits Explained',
        'Astrology vs Science', 'Famous Astrologers', 'Birth Chart Basics',
        'Love Compatibility', 'Career Predictions', 'Astrology in Indian Culture',
        'Numerology', 'Palmistry', 'Vastu Shastra'
    ],
    'FUNNY': [
        'Latest Funny Memes', 'Stand Up Comedy Clips', 'Hilarious Animal Videos',
        'Prank Videos', 'Funny Kids Moments', 'Comedy Skits',
        'Fails Compilation', 'Funny Dance Moves', 'Viral Jokes',
        'Comedy Roast', 'Parody Songs', 'Funny Voiceovers'
    ],
    'MEMES': [
        'Latest Funny Memes', 'Dank Memes', 'Viral Memes',
        'Classic Memes', 'Relatable Memes', 'Trending Meme Formats',
        'Meme History', 'Indian Memes', 'Wholesome Memes',
        'Savage Memes', 'Meme Challenges', 'Meme Reactions'
    ],
    'ANIME': [
        'Create an Anime Movie: Friendship Adventure',
        'Anime Battle: Heroes vs Villains',
        'Slice of Life: A Day in Tokyo',
        'Anime Romance: School Festival',
        'Anime Mystery: The Lost Artifact',
        'Anime Sports: The Underdog Team',
        'Anime Sci-Fi: Robots and Dreams',
        'Anime Fantasy: Magical Quest',
        'Anime Comedy: Everyday Laughs',
        'Anime Horror: Haunted School',
        'Anime Family: Sibling Bonds',
        'Anime Music: The Band Story'
    ]
}

# Track used topics in memory for this session
USED_TOPICS = set()

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
                # Remove used topics from fallback
                available = [t for t in FALLBACK_TOPICS[category_name] if t not in USED_TOPICS]
                if not available:
                    # Reset if all topics used
                    USED_TOPICS.clear()
                    available = FALLBACK_TOPICS[category_name][:]
                return available
            all_fallback = []
            for topics in FALLBACK_TOPICS.values():
                all_fallback.extend([t for t in topics if t not in USED_TOPICS])
            if not all_fallback:
                USED_TOPICS.clear()
            for topics in FALLBACK_TOPICS.values():
                all_fallback.extend(topics)
            return all_fallback

    def get_random_topic(self, category=None):
        topics = self.get_topics(category)
        if not topics:
            return None
        topic = random.choice(topics)
        USED_TOPICS.add(topic)
        return topic

if __name__ == "__main__":
    fetcher = TrendingTopicsFetcher(region='IN')
    
    print("\nFetching trends for all categories (will use fallback on error)...")
    all_trends = fetcher.get_topics()
    print(f"Sample topics: {all_trends[:5]}")
    
    print("\nGetting trending memes...")
    meme_topics = fetcher.get_topics('FUNNY')
    print(f"Sample meme topics: {meme_topics[:5]}")