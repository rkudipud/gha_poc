#!/usr/bin/env python3
"""
Sample Python file with complexity issues for testing the consistency checker.

This file intentionally contains various complexity violations to demonstrate
the code_complexity rule in action.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Optional, Any





class ComplexProcessor:
    """A class with too many methods to demonstrate class complexity checks."""
    
    def __init__(self):
        self.data = {}
        self.config = {}
        
    def method_1(self): pass
    def method_2(self): pass  
    def method_3(self): pass
    def method_4(self): pass
    def method_5(self): pass
    def method_6(self): pass
    def method_7(self): pass
    def method_8(self): pass
    def method_9(self): pass
    def method_10(self): pass
    def method_11(self): pass
    def method_12(self): pass
    def method_13(self): pass
    def method_14(self): pass
    def method_15(self): pass
    def method_16(self): pass
    def method_17(self): pass
    def method_18(self): pass
    def method_19(self): pass
    def method_20(self): pass
    def method_21(self): pass  # This should trigger the class complexity rule


def highly_complex_function(data: Dict[str, Any], options: Dict[str, Any]) -> Optional[str]:
    """
    A function with high cyclomatic complexity to demonstrate complexity checking.
    This function has many nested conditions and decision points.
    """
    if not data:
        if not options:
            return None
        else:
            if options.get('strict_mode'):
                if options.get('throw_errors'):
                    raise ValueError("No data provided")
                else:
                    return "error: no data"
            else:
                return "warning: no data"
    
    if data.get('type') == 'user':
        if data.get('active'):
            if data.get('verified'):
                if data.get('premium'):
                    if data.get('admin'):
                        return "admin_premium_user"
                    else:
                        return "premium_user"
                else:
                    if data.get('age', 0) > 18:
                        return "adult_user"
                    else:
                        return "minor_user"
            else:
                return "unverified_user"
        else:
            return "inactive_user"
    elif data.get('type') == 'system':
        if data.get('critical'):
            if data.get('automated'):
                return "critical_automated"
            else:
                return "critical_manual"
        else:
            return "non_critical_system"
    elif data.get('type') == 'guest':
        if data.get('temporary'):
            return "temp_guest"
        else:
            return "permanent_guest"
    else:
        if options.get('fallback_enabled'):
            return "unknown_with_fallback"
        else:
            return "unknown_type"


def very_long_function_with_many_lines():
    """
    This function is intentionally very long to test function length limits.
    It performs a series of operations that could be broken into smaller functions.
    """
    # Line 1: Initialize variables
    result = []
    counter = 0
    data_store = {}
    
    # Line 5: First processing block
    for i in range(100):
        if i % 2 == 0:
            counter += 1
            result.append(i * 2)
        else:
            result.append(i)
    
    # Line 13: Second processing block
    for item in result:
        if item > 50:
            data_store[item] = "high"
        elif item > 25:
            data_store[item] = "medium"
        else:
            data_store[item] = "low"
    
    # Line 22: Third processing block
    processed_data = []
    for key, value in data_store.items():
        if value == "high":
            processed_data.append(key * 3)
        elif value == "medium":
            processed_data.append(key * 2)
        else:
            processed_data.append(key)
    
    # Line 32: Fourth processing block
    final_result = []
    for item in processed_data:
        if item % 3 == 0:
            final_result.append(item / 3)
        elif item % 2 == 0:
            final_result.append(item / 2)
        else:
            final_result.append(item)
    
    # Line 42: Fifth processing block
    summary = {
        'total_items': len(final_result),
        'max_value': max(final_result) if final_result else 0,
        'min_value': min(final_result) if final_result else 0,
        'average': sum(final_result) / len(final_result) if final_result else 0
    }
    
    # Line 50: Sixth processing block
    if summary['average'] > 100:
        summary['category'] = 'high_average'
    elif summary['average'] > 50:
        summary['category'] = 'medium_average'
    else:
        summary['category'] = 'low_average'
    
    # Line 58: Seventh processing block - this function is getting too long!
    return {
        'data': final_result,
        'summary': summary,
        'metadata': {
            'processed_at': 'now',
            'version': '1.0',
            'algorithm': 'complex_processing'
        }
    }
    # This function should trigger the function length rule


def deeply_nested_function(level1, level2, level3, level4, level5):
    """Function with excessive nesting depth."""
    if level1:
        if level2:
            if level3:
                if level4:
                    if level5:
                        if level5 > 10:  # This is 6 levels deep!
                            return "too deep"
                        else:
                            return "deep enough"
                    else:
                        return "level5 false"
                else:
                    return "level4 false"
            else:
                return "level3 false"
        else:
            return "level2 false"
    else:
        return "level1 false"


def function_with_boolean_complexity(a, b, c, d, e):
    """Function with complex boolean operations."""
    # This creates high cyclomatic complexity due to boolean operators
    if (a and b) or (c and d) or (e and a) or (b and c) or (d and e):
        if (a or b) and (c or d) and (e or a) and (b or c) and (d or e):
            if not (a and b and c and d and e):
                return "complex boolean result"
    return "simple result"


# Module-level code that's also complex
def main():
    """Main function that ties everything together."""
    processor = ComplexProcessor()
    
    sample_data = {
        'type': 'user',
        'active': True,
        'verified': True,
        'premium': False,
        'age': 25
    }
    
    options = {
        'strict_mode': True,
        'throw_errors': False,
        'fallback_enabled': True
    }
    
    result = highly_complex_function(sample_data, options)
    long_result = very_long_function_with_many_lines()
    nested_result = deeply_nested_function(True, True, True, True, True)
    boolean_result = function_with_boolean_complexity(True, False, True, False, True)
    
    print(f"Complex function result: {result}")
    print(f"Long function result summary: {long_result['summary']}")
    print(f"Nested function result: {nested_result}")
    print(f"Boolean function result: {boolean_result}")


if __name__ == "__main__":
    main()
