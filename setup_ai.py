#!/usr/bin/env python3
"""
NeuroLMS AI Setup and Testing Script
"""

import os
import sys
from dotenv import load_dotenv

def setup_ai():
    """Setup AI configuration"""
    print("🤖 NeuroLMS AI Setup")
    print("=" * 50)

    # Check if .env exists
    if not os.path.exists('.env'):
        print("❌ .env file not found. Creating one...")
        create_env_file()
    else:
        print("✅ .env file found")

    # Load environment
    load_dotenv()

    # Check OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key == 'your_openai_api_key_here':
        print("\n🔑 OpenAI API Key Setup:")
        print("To use enhanced AI features, you need an OpenAI API key.")
        print("1. Visit: https://platform.openai.com/api-keys")
        print("2. Create a new API key")
        print("3. Add it to your .env file: OPENAI_API_KEY=your_key_here")
        print("\n⚠️  Without an API key, the system will use fallback methods.")

        setup_key = input("\nDo you want to enter your API key now? (y/n): ").lower().strip()
        if setup_key == 'y':
            key = input("Enter your OpenAI API key: ").strip()
            update_env_file('OPENAI_API_KEY', key)
            print("✅ API key saved!")
        else:
            print("ℹ️  You can add the API key later to .env file")
    else:
        print("✅ OpenAI API key configured")

    print("\n🧪 Testing AI Models...")
    test_ai_models()

def create_env_file():
    """Create a basic .env file"""
    env_content = """# NeuroLMS AI Configuration
# Add your OpenAI API key here for enhanced AI features
# Get your API key from: https://platform.openai.com/api-keys

OPENAI_API_KEY=your_openai_api_key_here

# AI Model Settings
AI_MODEL=gpt-3.5-turbo
MAX_TOKENS=1500
TEMPERATURE=0.7

# Risk Model Settings
RISK_MODEL_TRAIN_ON_STARTUP=true
RISK_MODEL_SAVE_PATH=models/

# Flask Settings
SECRET_KEY=your_secret_key_here_change_in_production

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/neurolms.log
"""

    with open('.env', 'w') as f:
        f.write(env_content)
    print("✅ Created .env file")

def update_env_file(key, value):
    """Update a specific key in .env file"""
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            lines = f.readlines()

        updated = False
        for i, line in enumerate(lines):
            if line.startswith(f'{key}='):
                lines[i] = f'{key}={value}\n'
                updated = True
                break

        if not updated:
            lines.append(f'{key}={value}\n')

        with open('.env', 'w') as f:
            f.writelines(lines)

def test_ai_models():
    """Test the AI models"""
    try:
        from ai_engine import ai_engine
        from risk_model import risk_model

        print("\n📝 Testing Script Enhancement...")
        test_script = "Machine learning is a subset of artificial intelligence"
        enhanced = ai_engine.enhance_script(test_script, "AI Fundamentals")
        print("✅ Script enhancement working" if len(enhanced) > len(test_script) else "⚠️  Using fallback method")

        print("🎯 Testing Risk Assessment...")
        risk_result = risk_model.predict_risk(75, 1, 120)
        print(f"✅ Risk assessment working - Score: {risk_result['risk_score']}, Level: {risk_result['risk_level']}")

        print("📊 Model Info:")
        model_info = risk_model.get_model_info()
        print(f"   - ML Model Trained: {model_info['is_trained']}")
        print(f"   - AI Engine Ready: {ai_engine.use_openai}")

        print("\n🎉 AI Setup Complete!")
        print("\nNext steps:")
        print("1. Run: python app.py")
        print("2. Visit: http://localhost:5000")
        print("3. Test the enhanced AI features!")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_ai_models()
        else:
            print("Usage: python setup_ai.py [test]")
    else:
        setup_ai()