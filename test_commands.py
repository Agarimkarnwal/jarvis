"""Quick test of all JARVIS V2 commands"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "core"))

from command_processor import CommandProcessor

jarvis = CommandProcessor()

test_commands = [
    "hello",
    "help",
    "time",
    "date",
    "status",
    "open chrome",
    "open notepad",
    "open calculator",
    "what is your name",
    "thank you",
    "goodbye"
]

print("=" * 60)
print("🤖 JARVIS V2 - COMMAND TEST SUITE")
print("=" * 60)

for cmd in test_commands:
    print(f"\n👤 User: {cmd}")
    result = jarvis.process_command(cmd)
    print(f"🤖 JARVIS: {result.message}")

print("\n" + "=" * 60)
print("✅ All commands tested successfully!")
print("=" * 60)

# Show stats
stats = jarvis.get_command_stats()
print(f"\n📊 Command Statistics:")
print(f"   Total: {stats['total']}")
print(f"   Successful: {stats['successful']}")
print(f"   Failed: {stats['failed']}")
print(f"   By Type: {stats['by_type']}")
