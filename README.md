# AI-Powered Content Creation Agent

This project is an AI agent that automates the creation and uploading of YouTube videos and Instagram Reels. The agent identifies trending topics, generates video scripts, creates videos with voiceovers, and uploads them to social media platforms.

## Features

-   **Trending Topic Discovery:** Identifies trending topics using various sources.
-   **Content Generation:** Automatically generates scripts, voiceovers, and video content.
-   **Automated Uploading:** Uploads the final videos to YouTube and Instagram.
-   **Cross-Platform:** Creates content for both long-form videos (YouTube) and short-form videos (Instagram Reels).

## Project Structure
```
.
├── README.md
├── requirements.txt
└── src
    ├── content_creation
    │   ├── __init__.py
    │   ├── script_generator.py
    │   ├── creator.py
    │   └── voice_generator.py
    ├── instagram
    │   ├── __init__.py
    │   └── uploader.py
    ├── main.py
    ├── trending
    │   ├── __init__.py
    │   └── google_trends.py
    └── youtube
        ├── __init__.py
        └── uploader.py
```