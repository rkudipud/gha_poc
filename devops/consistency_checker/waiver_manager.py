#!/usr/bin/env python3
"""
Waiver Manager for Consistency Checker Framework

This module provides comprehensive waiver management including:
- Multiple waiver types (line, pattern, rule-based)
- Expiration handling
- Approval workflows
- Waiver validation and reporting
"""

import re
import fnmatch
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import yaml
import json

from base_rule import Violation, Severity


class WaiverType(Enum):
    """Types of waivers supported"""
    LINE_SPECIFIC = "line_specific"
    PATTERN_BASED = "pattern_based"
    RULE_BASED = "rule_based"
    BULK = "bulk"
    TEMPORARY = "temporary"


@dataclass
class WaiverRule:
    """Waiver rule with comprehensive metadata"""
    # Identification
    id: str = ""
    type: WaiverType = WaiverType.LINE_SPECIFIC
    
    # Matching criteria
    pattern: str = ""
    rule_names: List[str] = field(default_factory=list)
    file_pattern: Optional[str] = None
    line_number: Optional[int] = None
    column: Optional[int] = None
    
    # Metadata
    reason: str = ""
    approved_by: str = ""
    created_date: Optional[date] = None
    expires: Optional[date] = None
    issue_reference: Optional[str] = None
    
    # Advanced matching
    code_content: Optional[str] = None  # Exact code to match
    message_pattern: Optional[str] = None  # Regex pattern for violation messages
    severity_filter: List[Severity] = field(default_factory=list)
    
    # Usage tracking
    usage_count: int = 0
    last_used: Optional[datetime] = None
    
    # Configuration overrides
    parameter_overrides: Dict[str, Any] = field(default_factory=dict)
    
    # Status
    active: bool = True
    
    def is_expired(self) -> bool:
        """Check if waiver has expired"""
        if not self.expires:
            return False
        return date.today() > self.expires
    
    def days_until_expiry(self) -> Optional[int]:
        """Get days until expiry (negative if expired)"""
        if not self.expires:
            return None
        delta = self.expires - date.today()
        return delta.days
    
    def matches_violation(self, violation: Violation, file_path: str) -> bool:
        """Check if this waiver applies to a specific violation"""
        if not self.active or self.is_expired():
            return False
        
        # Check rule name filter
        if self.rule_names and violation.rule_name not in self.rule_names:
            return False
        
        # Check severity filter
        if self.severity_filter and violation.severity not in self.severity_filter:
            return False
        
        # Type-specific matching
        if self.type == WaiverType.LINE_SPECIFIC:
            return self._matches_line_specific(violation, file_path)
        elif self.type == WaiverType.PATTERN_BASED:
            return self._matches_pattern_based(violation, file_path)
        elif self.type == WaiverType.RULE_BASED:
            return self._matches_rule_based(violation, file_path)
        elif self.type == WaiverType.BULK:
            return self._matches_bulk(violation, file_path)
        elif self.type == WaiverType.TEMPORARY:
            return self._matches_temporary(violation, file_path)
        
        return False
    
    def _matches_line_specific(self, violation: Violation, file_path: str) -> bool:
        """Match line-specific waivers"""
        # Check file path
        if self.file_pattern and not fnmatch.fnmatch(file_path, self.file_pattern):
            return False
        
        # Check line number
        if self.line_number is not None and violation.line_number != self.line_number:
            return False
        
        # Check column if specified
        if self.column is not None and violation.column != self.column:
            return False
        
        # Check code content if specified
        if self.code_content and self.code_content.strip() != violation.code_snippet.strip():
            return False
        
        # Check message pattern
        if self.message_pattern:
            if not re.search(self.message_pattern, violation.message):
                return False
        elif self.pattern and self.pattern not in violation.message:
            return False
        
        return True
    
    def _matches_pattern_based(self, violation: Violation, file_path: str) -> bool:
        """Match pattern-based waivers"""
        # Check file pattern
        if self.file_pattern and not fnmatch.fnmatch(file_path, self.file_pattern):
            return False
        
        # Check violation message or code
        if self.pattern:
            if self.pattern in violation.message or self.pattern in violation.code_snippet:
                return True
        
        # Check regex pattern
        if self.message_pattern:
            return bool(re.search(self.message_pattern, violation.message))
        
        return False
    
    def _matches_rule_based(self, violation: Violation, file_path: str) -> bool:
        """Match rule-based waivers"""
        # Check if rule matches
        if violation.rule_name not in self.rule_names:
            return False
        
        # Check file pattern if specified
        if self.file_pattern:
            return fnmatch.fnmatch(file_path, self.file_pattern)
        
        return True
    
    def _matches_bulk(self, violation: Violation, file_path: str) -> bool:
        """Match bulk waivers"""
        # Bulk waivers typically use file patterns
        if self.file_pattern and fnmatch.fnmatch(file_path, self.file_pattern):
            # Check if rule is included in bulk waiver
            if not self.rule_names or violation.rule_name in self.rule_names:
                return True
        
        return False
    
    def _matches_temporary(self, violation: Violation, file_path: str) -> bool:
        """Match temporary waivers"""
        # Similar to pattern-based but with expiration emphasis
        return self._matches_pattern_based(violation, file_path)
    
    def record_usage(self):
        """Record that this waiver was used"""
        self.usage_count += 1
        self.last_used = datetime.now()


class WaiverManager:
    """Rule-specific waiver management system (forward-compatible only)"""
    
    def __init__(self, rules_directory: Path):
        """
        Initialize waiver manager with rule-specific waiver files
        
        Args:
            rules_directory: Path to the rules directory containing rule subdirectories
        """
        self.rules_directory = rules_directory
        self.waivers: List[WaiverRule] = []
        self.statistics = {
            'total_waivers': 0,
            'expired_waivers': 0,
            'unused_waivers': 0,
            'waivers_by_type': {},
            'waivers_by_rule': {}
        }
        
        self.load_all_rule_waivers()
    
    def load_all_rule_waivers(self) -> None:
        """Load waivers from all rule-specific waiver files"""
        self.waivers = []
        
        if not self.rules_directory.exists():
            return
        
        # Scan for rule directories
        for rule_dir in self.rules_directory.iterdir():
            if rule_dir.is_dir() and rule_dir.name != '__pycache__':
                rule_name = rule_dir.name
                waiver_file = rule_dir / f"{rule_name}_waivers.yml"
                
                if waiver_file.exists():
                    try:
                        self._load_rule_waiver_file(waiver_file, rule_name)
                    except Exception as e:
                        print(f"Error loading waivers for rule {rule_name}: {e}")
        
        self._update_statistics()
    
    def _load_rule_waiver_file(self, waiver_file: Path, rule_name: str) -> None:
        """Load waivers from a specific rule's waiver file"""
        try:
            with open(waiver_file, 'r') as f:
                data = yaml.safe_load(f) or {}
            
            # Load rule-specific waivers (new format)
            rule_waivers = data.get('rule_waivers', [])
            for item in rule_waivers:
                waiver = self._parse_rule_waiver(item, rule_name)
                if waiver:
                    self.waivers.append(waiver)
            
            # Load file waivers (apply to any violation in matching files for this rule)
            file_waivers = data.get('file_waivers', [])
            for item in file_waivers:
                waiver = self._parse_file_waiver(item, rule_name)
                if waiver:
                    self.waivers.append(waiver)
            
            # Load line waivers (exact line/file matches for this rule)
            line_waivers = data.get('line_waivers', [])
            for item in line_waivers:
                waiver = self._parse_line_waiver(item, rule_name)
                if waiver:
                    self.waivers.append(waiver)
            
            # Load pattern waivers (message/code pattern matches for this rule)
            pattern_waivers = data.get('pattern_waivers', [])
            for item in pattern_waivers:
                waiver = self._parse_pattern_waiver(item, rule_name)
                if waiver:
                    self.waivers.append(waiver)
                    
        except Exception as e:
            print(f"Error loading waiver file {waiver_file}: {e}")
    
    def _parse_rule_waiver(self, item: Dict[str, Any], rule_name: str) -> Optional[WaiverRule]:
        """Parse rule-based waiver"""
        try:
            return WaiverRule(
                id=item.get('id', f"rule_{rule_name}_{len(self.waivers)}"),
                type=WaiverType.RULE_BASED,
                rule_names=[rule_name],  # Always scope to this rule
                file_pattern=item.get('scope') or item.get('file_pattern'),
                reason=item.get('reason', ''),
                approved_by=item.get('approved_by', ''),
                created_date=self._parse_date(item.get('created_date')),
                expires=self._parse_date(item.get('expires')),
                issue_reference=item.get('issue_reference'),
                parameter_overrides=item.get('parameter_overrides', {}),
                active=item.get('active', True)
            )
        except Exception as e:
            print(f"Error parsing rule waiver for {rule_name}: {e}")
            return None
    
    def _parse_file_waiver(self, item: Dict[str, Any], rule_name: str) -> Optional[WaiverRule]:
        """Parse file-based waiver (applies to all violations in matching files)"""
        try:
            return WaiverRule(
                id=item.get('id', f"file_{rule_name}_{len(self.waivers)}"),
                type=WaiverType.PATTERN_BASED,
                rule_names=[rule_name],
                file_pattern=item.get('pattern') or item.get('file_pattern'),
                reason=item.get('reason', ''),
                approved_by=item.get('approved_by', ''),
                created_date=self._parse_date(item.get('created_date')),
                expires=self._parse_date(item.get('expires')),
                issue_reference=item.get('issue_reference'),
                active=item.get('active', True)
            )
        except Exception as e:
            print(f"Error parsing file waiver for {rule_name}: {e}")
            return None
    
    def _parse_line_waiver(self, item: Dict[str, Any], rule_name: str) -> Optional[WaiverRule]:
        """Parse line-specific waiver"""
        try:
            return WaiverRule(
                id=item.get('id', f"line_{rule_name}_{len(self.waivers)}"),
                type=WaiverType.LINE_SPECIFIC,
                rule_names=[rule_name],
                file_pattern=item.get('file'),
                line_number=item.get('line'),
                column=item.get('column'),
                pattern=item.get('pattern', ''),
                reason=item.get('reason', ''),
                approved_by=item.get('approved_by', ''),
                created_date=self._parse_date(item.get('created_date')),
                expires=self._parse_date(item.get('expires')),
                issue_reference=item.get('issue_reference'),
                code_content=item.get('code_content'),
                message_pattern=item.get('message_pattern'),
                active=item.get('active', True)
            )
        except Exception as e:
            print(f"Error parsing line waiver for {rule_name}: {e}")
            return None
    
    def _parse_pattern_waiver(self, item: Dict[str, Any], rule_name: str) -> Optional[WaiverRule]:
        """Parse pattern-based waiver"""
        try:
            return WaiverRule(
                id=item.get('id', f"pattern_{rule_name}_{len(self.waivers)}"),
                type=WaiverType.PATTERN_BASED,
                rule_names=[rule_name],
                pattern=item.get('pattern', ''),
                file_pattern=item.get('file_pattern'),
                reason=item.get('reason', ''),
                approved_by=item.get('approved_by', ''),
                created_date=self._parse_date(item.get('created_date')),
                expires=self._parse_date(item.get('expires')),
                issue_reference=item.get('issue_reference'),
                message_pattern=item.get('message_pattern'),
                severity_filter=[Severity(s) for s in item.get('severity_filter', [])],
                active=item.get('active', True)
            )
        except Exception as e:
            print(f"Error parsing pattern waiver for {rule_name}: {e}")
            return None
        self.waivers = []
        
        for rule_name, waiver_file in self.rule_waiver_files.items():
            try:
                rule_waivers = self._load_rule_waivers(rule_name, waiver_file)
                self.waivers.extend(rule_waivers)
                print(f"✅ Loaded {len(rule_waivers)} waivers for rule '{rule_name}'")
            except Exception as e:
                print(f"❌ Error loading waivers for rule '{rule_name}': {e}")
        
        self._update_statistics()
        print(f"📊 Total waivers loaded: {len(self.waivers)}")
    
    def _load_rule_waivers(self, rule_name: str, waiver_file: Path) -> List[WaiverRule]:
        """Load waivers from a specific rule's waiver file"""
        if not waiver_file.exists():
            return []
        
        try:
            with open(waiver_file, 'r') as f:
                data = yaml.safe_load(f) or {}
            
            if not data:  # Empty file
                return []
            
            rule_waivers = []
            
            # Load different waiver types from the rule-specific file
            for item in data.get('line_waivers', []):
                waiver = self._parse_line_waiver(item, rule_name)
                if waiver:
                    rule_waivers.append(waiver)
            
            for item in data.get('pattern_waivers', []):
                waiver = self._parse_pattern_waiver(item, rule_name)
                if waiver:
                    rule_waivers.append(waiver)
            
            for item in data.get('rule_waivers', []):
                waiver = self._parse_rule_waiver(item, rule_name)
                if waiver:
                    rule_waivers.append(waiver)
            
            for item in data.get('bulk_waivers', []):
                waiver = self._parse_bulk_waiver(item, rule_name)
                if waiver:
                    rule_waivers.append(waiver)
            

            
            return rule_waivers
            
        except Exception as e:
            print(f"Error loading waivers from {waiver_file}: {e}")
            return []
    
    def _parse_line_waiver(self, item: Dict[str, Any], rule_name: str) -> Optional[WaiverRule]:
        """Parse line-specific waiver"""
        try:
            # Handle violation_line format like "file:line:col: rule message"
            violation_line = item.get('violation_line', '')
            if violation_line:
                parts = violation_line.split(':', 3)
                if len(parts) >= 4:
                    file_pattern = parts[0]
                    line_number = int(parts[1]) if parts[1].isdigit() else None
                    column = int(parts[2]) if parts[2].isdigit() else None
                    message_part = parts[3].strip()
                else:
                    file_pattern = None
                    line_number = None
                    column = None
                    message_part = violation_line
            else:
                file_pattern = item.get('file_pattern')
                line_number = item.get('line_number')
                column = item.get('column')
                message_part = item.get('pattern', '')
            
            # Include the rule name in the waiver
            waiver_rule_names = item.get('rules', [rule_name])
            if rule_name not in waiver_rule_names:
                waiver_rule_names.append(rule_name)
            
            return WaiverRule(
                id=item.get('id', f"line_{rule_name}_{len(self.waivers)}"),
                type=WaiverType.LINE_SPECIFIC,
                pattern=message_part,
                rule_names=waiver_rule_names,
                file_pattern=file_pattern,
                line_number=line_number,
                column=column,
                reason=item.get('reason', ''),
                approved_by=item.get('approved_by', ''),
                created_date=self._parse_date(item.get('created_date')),
                expires=self._parse_date(item.get('expires')),
                issue_reference=item.get('issue_reference'),
                code_content=item.get('code_content'),
                message_pattern=item.get('message_pattern'),
                active=item.get('active', True)
            )
        except Exception as e:
            print(f"Error parsing line waiver for rule {rule_name}: {e}")
            return None
    
    def _parse_pattern_waiver(self, item: Dict[str, Any], rule_name: str) -> Optional[WaiverRule]:
        """Parse pattern-based waiver"""
        try:
            # Include the rule name in the waiver
            waiver_rule_names = item.get('rules', [rule_name])
            if rule_name not in waiver_rule_names:
                waiver_rule_names.append(rule_name)
                
            return WaiverRule(
                id=item.get('id', f"pattern_{rule_name}_{len(self.waivers)}"),
                type=WaiverType.PATTERN_BASED,
                pattern=item.get('pattern', ''),
                rule_names=waiver_rule_names,
                file_pattern=item.get('file_pattern'),
                reason=item.get('reason', ''),
                approved_by=item.get('approved_by', ''),
                created_date=self._parse_date(item.get('created_date')),
                expires=self._parse_date(item.get('expires')),
                issue_reference=item.get('issue_reference'),
                message_pattern=item.get('message_pattern'),
                severity_filter=[Severity(s) for s in item.get('severity_filter', [])],
                active=item.get('active', True)
            )
        except Exception as e:
            print(f"Error parsing pattern waiver for rule {rule_name}: {e}")
            return None
    
    def _parse_rule_waiver(self, item: Dict[str, Any], rule_name: str) -> Optional[WaiverRule]:
        """Parse rule-based waiver"""
        try:
            # Include the rule name in the waiver
            waiver_rule_names = item.get('rules', [])
            if item.get('rule'):
                waiver_rule_names = [item.get('rule')]
            if not waiver_rule_names:
                waiver_rule_names = [rule_name]
            elif rule_name not in waiver_rule_names:
                waiver_rule_names.append(rule_name)
            
            return WaiverRule(
                id=item.get('id', f"rule_{rule_name}_{len(self.waivers)}"),
                type=WaiverType.RULE_BASED,
                rule_names=waiver_rule_names,
                file_pattern=item.get('scope') or item.get('file_pattern'),
                reason=item.get('reason', ''),
                approved_by=item.get('approved_by', ''),
                created_date=self._parse_date(item.get('created_date')),
                expires=self._parse_date(item.get('expires')),
                issue_reference=item.get('issue_reference'),
                parameter_overrides=item.get('parameter_overrides', {}),
                active=item.get('active', True)
            )
        except Exception as e:
            print(f"Error parsing rule waiver for rule {rule_name}: {e}")
            return None
    
    def _parse_bulk_waiver(self, item: Dict[str, Any], rule_name: str) -> Optional[WaiverRule]:
        """Parse bulk waiver"""
        try:
            rules = item.get('rules', [rule_name])
            if rules == "*":
                rules = [rule_name]  # Apply to current rule instead of all rules
            elif rule_name not in rules:
                rules.append(rule_name)
            
            return WaiverRule(
                id=item.get('id', f"bulk_{rule_name}_{len(self.waivers)}"),
                type=WaiverType.BULK,
                pattern=item.get('pattern', ''),
                rule_names=rules,
                file_pattern=item.get('pattern'),  # Use pattern as file pattern for bulk
                reason=item.get('reason', ''),
                approved_by=item.get('approved_by', ''),
                created_date=self._parse_date(item.get('created_date')),
                expires=self._parse_date(item.get('expires')),
                issue_reference=item.get('issue_reference'),
                active=item.get('active', True)
            )
        except Exception as e:
            print(f"Error parsing bulk waiver for rule {rule_name}: {e}")
            return None
    

    
    def save_rule_waivers(self, rule_name: str, waivers: List[WaiverRule]) -> bool:
        """Save waivers for a specific rule to its waiver file"""
        if rule_name not in self.rule_waiver_files:
            # Create new waiver file for the rule
            if not self.rules_directory:
                print(f"❌ Cannot save waivers for rule '{rule_name}': No rules directory configured")
                return False
            
            rule_dir = self.rules_directory / rule_name
            if not rule_dir.exists():
                print(f"❌ Cannot save waivers for rule '{rule_name}': Rule directory not found")
                return False
            
            waiver_file = rule_dir / f"{rule_name}_waivers.yml"
            self.rule_waiver_files[rule_name] = waiver_file
        
        waiver_file = self.rule_waiver_files[rule_name]
        
        try:
            # Group waivers by type
            data = {
                'line_waivers': [],
                'pattern_waivers': [],
                'rule_waivers': [],
                'bulk_waivers': []
            }
            
            for waiver in waivers:
                waiver_dict = {
                    'id': waiver.id,
                    'reason': waiver.reason,
                    'approved_by': waiver.approved_by,
                    'created_date': waiver.created_date.isoformat() if waiver.created_date else None,
                    'expires': waiver.expires.isoformat() if waiver.expires else None,
                    'active': waiver.active,
                    'issue_reference': waiver.issue_reference
                }
                
                if waiver.type == WaiverType.LINE_SPECIFIC:
                    waiver_dict.update({
                        'file_pattern': waiver.file_pattern,
                        'line_number': waiver.line_number,
                        'column': waiver.column,
                        'pattern': waiver.pattern,
                        'code_content': waiver.code_content,
                        'message_pattern': waiver.message_pattern
                    })
                    data['line_waivers'].append(waiver_dict)
                    
                elif waiver.type == WaiverType.PATTERN_BASED:
                    waiver_dict.update({
                        'pattern': waiver.pattern,
                        'file_pattern': waiver.file_pattern,
                        'message_pattern': waiver.message_pattern,
                        'severity_filter': [s.value for s in waiver.severity_filter]
                    })
                    data['pattern_waivers'].append(waiver_dict)
                    
                elif waiver.type == WaiverType.RULE_BASED:
                    waiver_dict.update({
                        'rule': rule_name,
                        'scope': waiver.file_pattern,
                        'parameter_overrides': waiver.parameter_overrides
                    })
                    data['rule_waivers'].append(waiver_dict)
                    
                elif waiver.type == WaiverType.BULK:
                    waiver_dict.update({
                        'pattern': waiver.pattern,
                        'rules': waiver.rule_names
                    })
                    data['bulk_waivers'].append(waiver_dict)
            
            # Remove empty sections
            data = {k: v for k, v in data.items() if v}
            
            with open(waiver_file, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            
            print(f"✅ Saved {len(waivers)} waivers for rule '{rule_name}' to {waiver_file}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving waivers for rule '{rule_name}': {e}")
            return False
    
    def apply_waivers(self, violations: List[Violation], file_path: str) -> Tuple[List[Violation], List[Violation]]:
        """
        Apply waivers to violations
        
        Returns:
            Tuple of (remaining_violations, waived_violations)
        """
        remaining_violations = []
        waived_violations = []
        
        for violation in violations:
            waived = False
            
            for waiver in self.waivers:
                if waiver.matches_violation(violation, file_path):
                    waiver.record_usage()
                    waived_violations.append(violation)
                    waived = True
                    break
            
            if not waived:
                remaining_violations.append(violation)
        
        return remaining_violations, waived_violations
    
    def get_waiver_statistics(self) -> Dict[str, Any]:
        """Get comprehensive waiver statistics"""
        self._update_statistics()
        
        # Add used/unused breakdown
        used_waivers = sum(1 for w in self.waivers if w.usage_count > 0)
        self.statistics.update({
            'used_waivers': used_waivers,
        })
        
        return self.statistics
    
    def get_unused_waivers_by_rule(self) -> Dict[str, int]:
        """Get count of unused waivers per rule"""
        unused_by_rule = {}
        for waiver in self.waivers:
            if waiver.usage_count == 0:
                for rule_name in waiver.rule_names:
                    unused_by_rule[rule_name] = unused_by_rule.get(rule_name, 0) + 1
        return unused_by_rule
    
    def get_used_waivers_by_rule(self) -> Dict[str, int]:
        """Get count of used waivers per rule"""
        used_by_rule = {}
        for waiver in self.waivers:
            if waiver.usage_count > 0:
                for rule_name in waiver.rule_names:
                    used_by_rule[rule_name] = used_by_rule.get(rule_name, 0) + 1
        return used_by_rule
    
    def get_expiring_waivers(self, days: int = 14) -> List[WaiverRule]:
        """Get waivers expiring within specified days"""
        expiring = []
        for waiver in self.waivers:
            days_left = waiver.days_until_expiry()
            if days_left is not None and 0 < days_left <= days:
                expiring.append(waiver)
        return sorted(expiring, key=lambda w: w.days_until_expiry() or 0)
    
    def get_expired_waivers(self) -> List[WaiverRule]:
        """Get all expired waivers"""
        return [w for w in self.waivers if w.is_expired()]
    
    def get_unused_waivers(self) -> List[WaiverRule]:
        """Get waivers that haven't been used"""
        return [w for w in self.waivers if w.usage_count == 0]
    
    def validate_waivers(self) -> Dict[str, List[str]]:
        """Validate all waivers and return issues"""
        issues = {
            'expired': [],
            'invalid_patterns': [],
            'missing_approval': [],
            'unused': [],
            'duplicate': []
        }
        
        seen_waivers = set()
        
        for waiver in self.waivers:
            # Check expiration
            if waiver.is_expired():
                issues['expired'].append(f"Waiver {waiver.id} expired on {waiver.expires}")
            
            # Check approval
            if not waiver.approved_by:
                issues['missing_approval'].append(f"Waiver {waiver.id} missing approval")
            
            # Check if unused
            if waiver.usage_count == 0:
                issues['unused'].append(f"Waiver {waiver.id} never used")
            
            # Check for duplicates
            waiver_key = (waiver.pattern, waiver.file_pattern, waiver.line_number, tuple(waiver.rule_names))
            if waiver_key in seen_waivers:
                issues['duplicate'].append(f"Waiver {waiver.id} is duplicate")
            seen_waivers.add(waiver_key)
            
            # Validate patterns
            try:
                if waiver.message_pattern:
                    re.compile(waiver.message_pattern)
            except re.error as e:
                issues['invalid_patterns'].append(f"Waiver {waiver.id} has invalid regex: {e}")
        
        return issues
    
    def _parse_date(self, date_str: Optional[Union[str, date]]) -> Optional[date]:
        """Parse date string into a date object"""
        if not date_str:
            return None
        
        if isinstance(date_str, date):
            return date_str
        
        if isinstance(date_str, str):
            try:
                # Try common date formats
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']:
                    try:
                        parsed = datetime.strptime(date_str, fmt)
                        return parsed.date()
                    except ValueError:
                        continue
                
                # Try ISO format
                if 'T' in date_str:
                    parsed = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    return parsed.date()
                
                # Try basic YYYY-MM-DD
                parts = date_str.split('-')
                if len(parts) == 3:
                    return date(int(parts[0]), int(parts[1]), int(parts[2]))
                    
            except (ValueError, IndexError) as e:
                print(f"Warning: Could not parse date '{date_str}': {e}")
                return None
        
        return None
    
    def create_waiver_from_violation(
        self,
        violation: Violation,
        file_path: str,
        reason: str,
        approved_by: str,
        expires_days: Optional[int] = 90
    ) -> WaiverRule:
        """Create a new waiver from a violation"""
        expires_date = None
        if expires_days:
            expires_date = date.today() + timedelta(days=expires_days)
        
        waiver = WaiverRule(
            id=f"auto_{violation.rule_name}_{len(self.waivers)}",
            type=WaiverType.LINE_SPECIFIC,
            pattern=violation.message,
            rule_names=[violation.rule_name],
            file_pattern=file_path,
            line_number=violation.line_number,
            column=violation.column,
            reason=reason,
            approved_by=approved_by,
            created_date=date.today(),
            expires=expires_date,
            code_content=violation.code_snippet,
            active=True
        )
        
        self.waivers.append(waiver)
        return waiver
    
    def save_waivers(self) -> None:
        """Save waivers back to file"""
        if not self.waiver_file:
            return
        
        # Group waivers by type
        line_waivers = []
        pattern_waivers = []
        rule_waivers = []
        bulk_waivers = []
        
        for waiver in self.waivers:
            waiver_dict = {
                'id': waiver.id,
                'reason': waiver.reason,
                'approved_by': waiver.approved_by,
                'active': waiver.active
            }
            
            if waiver.created_date:
                waiver_dict['created_date'] = waiver.created_date.strftime('%Y-%m-%d')
            if waiver.expires:
                waiver_dict['expires'] = waiver.expires.strftime('%Y-%m-%d')
            if waiver.issue_reference:
                waiver_dict['issue_reference'] = waiver.issue_reference
            
            if waiver.type == WaiverType.LINE_SPECIFIC:
                waiver_dict.update({
                    'file_pattern': waiver.file_pattern,
                    'line_number': waiver.line_number,
                    'column': waiver.column,
                    'pattern': waiver.pattern,
                    'code_content': waiver.code_content
                })
                line_waivers.append(waiver_dict)
            
            elif waiver.type == WaiverType.PATTERN_BASED:
                waiver_dict.update({
                    'pattern': waiver.pattern,
                    'file_pattern': waiver.file_pattern,
                    'rules': waiver.rule_names,
                    'message_pattern': waiver.message_pattern
                })
                pattern_waivers.append(waiver_dict)
            
            elif waiver.type == WaiverType.RULE_BASED:
                waiver_dict.update({
                    'rules': waiver.rule_names,
                    'file_pattern': waiver.file_pattern,
                    'parameter_overrides': waiver.parameter_overrides
                })
                rule_waivers.append(waiver_dict)
            
            elif waiver.type == WaiverType.BULK:
                waiver_dict.update({
                    'pattern': waiver.file_pattern,
                    'rules': waiver.rule_names if waiver.rule_names else "*"
                })
                bulk_waivers.append(waiver_dict)
        
        # Create output structure
        output = {
            'settings': {
                'default_expiry_days': 90,
                'expiry_warning_days': 14,
                'max_waivers_per_file': 10
            }
        }
        
        if line_waivers:
            output['line_waivers'] = line_waivers
        if pattern_waivers:
            output['pattern_waivers'] = pattern_waivers
        if rule_waivers:
            output['rule_waivers'] = rule_waivers
        if bulk_waivers:
            output['bulk_waivers'] = bulk_waivers
        
        # Write to file
        with open(self.waiver_file, 'w') as f:
            yaml.dump(output, f, default_flow_style=False, sort_keys=False)
    
    def _update_statistics(self) -> None:
        """Update internal statistics"""
        total = len(self.waivers)
        expired = sum(1 for w in self.waivers if w.is_expired())
        unused = sum(1 for w in self.waivers if w.usage_count == 0)
        
        # Count by type
        by_type = {}
        for waiver in self.waivers:
            type_name = waiver.type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1
        
        # Count by rule
        by_rule = {}
        for waiver in self.waivers:
            for rule_name in waiver.rule_names:
                by_rule[rule_name] = by_rule.get(rule_name, 0) + 1
        
        self.statistics = {
            'total_waivers': total,
            'expired_waivers': expired,
            'unused_waivers': unused,
            'active_waivers': total - expired,
            'waivers_by_type': by_type,
            'waivers_by_rule': by_rule,
            'expiring_soon': sum(1 for w in self.waivers 
                               if w.days_until_expiry() is not None and 0 < w.days_until_expiry() <= 14)
        }
