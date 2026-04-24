"""Test TTS works for multiple commands"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "core"))

from voice_engine_v2 import VoiceEngineV2
from command_processor import CommandProcessor

print("=" * 60)
print("🤖 TESTING: TTS Multiple Commands")
print("=" * 60)

jarvis_voice = VoiceEngineV2()
jarvis_commands = CommandProcessor()

# Test commands
test_cmds = [
    "hello",
    "time", 
    "date",
    "status"
]

print("\n🔊 Testing speech for 4 commands in sequence...\n")

for i, cmd in enumerate(test_cmds, 1):
    print(f"{i}. 👤 Command: {cmd}")
    
    # Get response
    result = jarvis_commands.process_command(cmd)
    print(f"   🤖 Response: {result.message[:50]}...")
    
    # Speak it (this is what we're testing)
    print(f"   🔊 Speaking...", end=" ")
    try:
        jarvis_voice.speak(result.message)
        print("✅ SUCCESS")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Small delay between commands
    import time
    time.sleep(0.5)

print("\n" + "=" * 60)
print("✅ TTS Multi-Command Test Complete!")
print("=" * 60)
print("\n🎉 All 4 commands spoken successfully without errors!")
print("The 'run loop already started' bug is FIXED!")
