#!/usr/bin/env python3
"""
Consistency Checker Framework Demo

This script demonstrates the capabilities of the consistency checker.
Run this to see the new features in action.
"""

import sys
from pathlib import Path

# Add the consistency checker to the path
sys.path.insert(0, str(Path(__file__).parent))

from checker import app

if __name__ == "__main__":
    print("Consistency Checker Framework")
    print("=====================================")
    print()
    print("Available commands:")
    print("  list-rules       - Show all available rules with status")
    print("  run-all          - Run all enabled rules")
    print("  run-rule <name>  - Run a specific rule")
    print("  show-waivers     - Display configured waivers")
    print("  validate-waivers - Check waiver configuration")
    print("  config           - Show current configuration")
    print("  stats            - Show system statistics")
    print()
    print("Example usage:")
    print("  python demo.py list-rules --verbose")
    print("  python demo.py run-all --format html --output report.html")
    print("  python demo.py run-rule code_complexity --fix")
    print("  python demo.py show-waivers --expiring 30")
    print()
    
    # If no arguments provided, show the help
    if len(sys.argv) == 1:
        sys.argv.append("--help")
    
    # Run the CLI
    app()
