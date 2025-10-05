#!/usr/bin/env python3
"""
Test script to debug OpenAI client initialization in the bot context
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Loaded environment variables from {env_file}")
    else:
        print(f"⚠️ No .env file found at {env_file}")
except ImportError:
    print("⚠️ python-dotenv not installed, skipping .env file loading")
except Exception as e:
    print(f"❌ Error loading .env file: {e}")

def test_openai_client():
    """Test OpenAI client creation"""
    print("\n🧪 Testing OpenAI Client Creation:")
    print("=" * 40)
    
    # Check environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"OPENAI_API_KEY found: {'Yes' if api_key else 'No'}")
    if api_key:
        print(f"Key length: {len(api_key)}")
        print(f"Key starts with: {api_key[:10]}...")
    
    # Test import
    try:
        import openai
        print(f"✅ OpenAI module imported successfully (v{openai.__version__})")
    except ImportError as e:
        print(f"❌ Failed to import OpenAI: {e}")
        return
    
    # Test client creation
    try:
        if api_key and openai:
            client = openai.AsyncOpenAI(api_key=api_key)
            print("✅ OpenAI AsyncClient created successfully!")
            return True
        else:
            print("❌ Cannot create client - missing API key or module")
            return False
    except Exception as e:
        print(f"❌ Error creating OpenAI client: {e}")
        return False

def test_enhanced_processor():
    """Test the actual EnhancedMessageProcessor"""
    print("\n🤖 Testing EnhancedMessageProcessor:")
    print("=" * 40)
    
    try:
        from DefHack.clarity_opsbot.enhanced_processor import EnhancedMessageProcessor
        import logging
        
        # Create logger
        logger = logging.getLogger("test")
        
        # Create processor
        processor = EnhancedMessageProcessor(logger)
        print("✅ EnhancedMessageProcessor created")
        
        # Test getting OpenAI client
        client = processor._get_openai_client()
        if client:
            print("✅ OpenAI client obtained from processor!")
            return True
        else:
            print("❌ OpenAI client is None")
            return False
            
    except Exception as e:
        print(f"❌ Error testing processor: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 DefHack OpenAI Client Debug Test")
    print("=" * 50)
    
    # Test direct client creation
    client_works = test_openai_client()
    
    # Test processor
    processor_works = test_enhanced_processor()
    
    print("\n📊 Summary:")
    print("=" * 20)
    print(f"Direct client creation: {'✅ PASS' if client_works else '❌ FAIL'}")
    print(f"Processor client:       {'✅ PASS' if processor_works else '❌ FAIL'}")
    
    if client_works and processor_works:
        print("\n🎉 All tests passed! OpenAI should work in the bot.")
    else:
        print("\n⚠️ Issues found. OpenAI integration needs fixing.")