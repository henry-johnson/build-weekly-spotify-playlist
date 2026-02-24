import os
import sys
import base64
import urllib.request
from pathlib import Path
from datetime import datetime

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from model_provider_openai import OpenAIProvider
from config import (
    OPENAI_TEXT_MODEL_SMALL,
    OPENAI_TEXT_MODEL_LARGE,
    OPENAI_IMAGE_MODEL,
    OPENAI_TEMPERATURE_SMALL,
    OPENAI_TEMPERATURE_LARGE,
)

def test_text_generation_small():
    """Test gpt-5-nano for descriptions"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return False
    
    provider = OpenAIProvider(api_key=api_key)
    system_prompt = "You are a playlist description writer."
    user_prompt = "Write a one-line description of a chill music playlist."
    
    try:
        response = provider.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=OPENAI_TEXT_MODEL_SMALL,
            temperature=OPENAI_TEMPERATURE_SMALL
        )
        content = response["choices"][0]["message"]["content"]
        print(f"✅ gpt-5-nano result: {content[:100]}...")
        return True
    except Exception as e:
        print(f"❌ gpt-5-nano failed: {e}")
        return False

def test_text_generation_large():
    """Test gpt-5.2 for recommendations"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return False
    
    provider = OpenAIProvider(api_key=api_key)
    system_prompt = "Return JSON only, no markdown."
    user_prompt = 'Generate 3 Spotify search queries: {"queries": ["query1", "query2", "query3"]}'
    
    try:
        response = provider.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=OPENAI_TEXT_MODEL_LARGE,
            temperature=OPENAI_TEMPERATURE_LARGE
        )
        content = response["choices"][0]["message"]["content"]
        print(f"✅ gpt-5.2 result: {content[:100]}...")
        return True
    except Exception as e:
        print(f"❌ gpt-5.2 failed: {e}")
        return False

def test_image_generation():
    """Test chatgpt-image-latest for artwork"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return False
    
    provider = OpenAIProvider(api_key=api_key)
    prompt = "Soft pastel gradient: spring greens and pinks flowing into summer golds and blues."
    
    try:
        response = provider.generate_image(
            prompt=prompt,
            model=OPENAI_IMAGE_MODEL,
            size="1024",
            quality="low"
        )
        image_data = response["data"][0]
        
        # OpenAI returns either b64_json or url depending on response_format
        if "b64_json" in image_data:
            b64_image = image_data["b64_json"]
            image_bytes = base64.b64decode(b64_image)
            size_kb = len(image_bytes) / 1024
            print(f"✅ Image generated (b64): {size_kb:.1f} KB")
            
            # Save to disk with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path(__file__).parent / f"generated_artwork_{timestamp}.jpg"
            output_path.write_bytes(image_bytes)
            print(f"   Saved to: {output_path}")
        elif "url" in image_data:
            # Download URL-based image
            url = image_data["url"]
            print(f"✅ Image generated (URL): {url[:50]}...")
            
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = f"generated_artwork_{timestamp}.jpg"
                urllib.request.urlretrieve(url, filepath)
                print(f"   Downloaded to: {filepath}")
            except Exception as e:
                print(f"   Could not download: {e}")
        else:
            print(f"❌ Unexpected image response format: {image_data.keys()}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Image generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing OpenAI Provider...\n")
    
    results = [
        ("Text (small)", test_text_generation_small()),
        ("Text (large)", test_text_generation_large()),
        ("Image", test_image_generation()),
    ]
    
    print("\n" + "="*50)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(r[1] for r in results)
    sys.exit(0 if all_passed else 1)
