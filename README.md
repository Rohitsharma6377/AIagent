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

## 3D Anime Movie Pipeline (Semi-Automated)

This project can help you create a 3D anime-style movie with:
- Multi-character script and voices
- Scene breakdowns (Japan, India, China backgrounds)
- Automated voice generation
- Automated Blender Python scripts for scene assembly and animation
- Instructions for using free 3D models and environments

### How It Works
1. **Script Generation**: The pipeline generates a multi-character script and splits it into scenes.
2. **Voice Generation**: Each character's lines are converted to audio using free TTS APIs.
3. **Scene Breakdown**: For each scene, the script suggests a location (Japan, India, China) and which characters are present.
4. **3D Assets**: You download free 3D character models (ReadyPlayerMe, VRoid, Mixamo) and environments (Sketchfab, Poly Haven).
5. **Blender Automation**: The pipeline generates Blender Python scripts to:
   - Load the 3D environment and characters
   - Place characters in the scene
   - Animate basic actions (walk, talk, gesture)
   - Sync mouth movement to generated audio
   - Render the scene to video
6. **Assembly**: The rendered scenes and audio are combined into a full movie.

### Free Resources for 3D Assets
- [ReadyPlayerMe](https://readyplayer.me/): Free 3D avatars
- [VRoid Studio](https://vroid.com/en/studio): Anime-style 3D character creator
- [Mixamo](https://www.mixamo.com/): Free auto-rigging and animation for 3D characters
- [Sketchfab](https://sketchfab.com/): Free 3D environments and props
- [Poly Haven](https://polyhaven.com/): Free HDRIs, textures, and 3D models

### How to Use
1. **Install Blender** (https://www.blender.org/download/)
2. **Run the AIagent pipeline** to generate scripts, voices, and Blender scripts.
3. **Download 3D models/environments** as suggested by the pipeline.
4. **Run the generated Blender scripts** to assemble and render each scene.
5. **Combine the rendered scenes and audio** using MoviePy or your preferred video editor.

### Limitations
- Full 3D animation cannot be 100% automated with free tools/APIs; some manual steps are required.
- The pipeline automates as much as possible: script, voice, scene breakdown, and Blender scripting.
- You may need to adjust character placement or animation in Blender for best results.