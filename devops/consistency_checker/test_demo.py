#!/usr/bin/env python3
"""
Quick test of the consistency checker system
"""

import sys
from pathlib import Path

# Test rule loading
try:
    from rules.code_complexity.code_complexity import CodeComplexity
    rule = CodeComplexity()
    print("✅ Code complexity rule loaded successfully!")
    print(f"   Rule name: {rule.metadata().name}")
    print(f"   Rule description: {rule.metadata().description}")
    print(f"   Rule category: {rule.metadata().category}")
    print()
except Exception as e:
    print(f"❌ Error loading code complexity rule: {e}")
    print()

# Test basic functionality
try:
    from checker import ConsistencyChecker
    checker = ConsistencyChecker()
    print("✅ Consistency checker loaded successfully!")
    
    # Test on sample code
    sample_file = Path("../../working/sample_complex_code.py")
    if sample_file.exists():
        print(f"✅ Sample file found: {sample_file}")
        
        # Run code complexity check on sample file
        result = rule.check(Path("../.."), [sample_file])
        print(f"✅ Rule execution completed!")
        print(f"   Files checked: {len(result.files_checked)}")
        print(f"   Violations found: {len(result.violations)}")
        
        if result.violations:
            print("\n📋 Violations found:")
            for i, violation in enumerate(result.violations[:3], 1):  # Show first 3
                print(f"   {i}. {violation.message}")
                print(f"      File: {violation.file_path}:{violation.line}")
                print(f"      Severity: {violation.severity.value}")
            
            if len(result.violations) > 3:
                print(f"   ... and {len(result.violations) - 3} more")
        else:
            print("   No violations found.")
    else:
        print(f"❌ Sample file not found: {sample_file}")
        
except Exception as e:
    print(f"❌ Error in test: {e}")
    import traceback
    traceback.print_exc()

print("\n🎯 Consistency Checker Test Complete!")
print("\nNext steps:")
print("  1. Fix any rule loading issues")
print("  2. Run: python demo.py list-rules --verbose")
print("  3. Run: python demo.py run-all --format console")
