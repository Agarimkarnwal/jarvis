"""Interactive JARVIS Test - Type Your Commands!"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from main_simple import SimpleJARVIS
import time

print("=" * 60)
print("🤖 JARVIS INTERACTIVE TEST MODE")
print("=" * 60)
print("Type commands and press ENTER")
print("Commands: status | time | date | hello | help | open notepad | quit")
print("-" * 60)

jarvis = SimpleJARVIS()

while True:
    try:
        cmd = input("\n👤 You: ").strip().lower()
        
        if not cmd:
            continue
        if cmd in ['quit', 'exit', 'bye']:
            print("🤖 JARVIS: Goodbye!")
            break
            
        print("🤖 JARVIS: Processing...")
        jarvis.execute_command(cmd)
        
    except KeyboardInterrupt:
        print("\n🤖 JARVIS: Goodbye!")
        break
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n✅ Test completed!")
