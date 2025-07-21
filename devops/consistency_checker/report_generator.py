#!/usr/bin/env python3
"""
Report Generator for Consistency Checker Framework

This module generates comprehensive reports in various formats:
- Console output with Rich formatting
- HTML reports with interactive features
- JSON reports for CI/CD integration
- CSV reports for data analysis
"""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import asdict
from jinja2 import Template

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree
from rich.progress import Progress, BarColumn, TimeElapsedColumn
from rich.syntax import Syntax
from rich.layout import Layout
from rich.align import Align

from base_rule import CheckResult, Violation, Severity
from waiver_manager import WaiverManager, WaiverRule


class ReportGenerator:
    """Generate comprehensive consistency check reports"""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.report_data = {}
    
    def generate_console_report(
        self,
        results: List[CheckResult],
        waiver_manager: Optional[WaiverManager] = None,
        show_details: bool = True,
        show_waivers: bool = True
    ) -> int:
        """Generate rich console report and return exit code"""
        
        # Prepare summary statistics
        self._prepare_report_data(results, waiver_manager)
        
        # Show header
        self._show_header()
        
        # Show rule status table
        self._show_rule_status_table(results, waiver_manager)
        
        # Show detailed violations if requested
        if show_details:
            self._show_violation_details(results)
        
        # Show waiver information if available
        if show_waivers and waiver_manager:
            self._show_waiver_summary(waiver_manager)
        
        # Show final summary
        exit_code = self._show_final_summary()
        
        return exit_code
    
    def _prepare_report_data(
        self,
        results: List[CheckResult],
        waiver_manager: Optional[WaiverManager]
    ) -> None:
        """Prepare consolidated report data"""
        total_rules = len(results)
        passed_rules = sum(1 for r in results if r.passed)
        failed_rules = total_rules - passed_rules
        
        total_violations = sum(len(r.violations) for r in results)
        total_warnings = sum(len(r.warnings) for r in results)
        total_waived = sum(r.waiver_count for r in results)
        
        execution_time = sum(r.execution_time for r in results)
        
        # Categorize violations by severity
        violations_by_severity = {
            Severity.CRITICAL: 0,
            Severity.ERROR: 0,
            Severity.WARNING: 0,
            Severity.INFO: 0
        }
        
        for result in results:
            for violation in result.violations:
                violations_by_severity[violation.severity] += 1
        
        # Files checked
        files_checked = sum(r.files_checked for r in results)
        lines_checked = sum(r.lines_checked for r in results)
        
        self.report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_rules': total_rules,
                'passed_rules': passed_rules,
                'failed_rules': failed_rules,
                'total_violations': total_violations,
                'total_warnings': total_warnings,
                'total_waived': total_waived,
                'execution_time': execution_time,
                'files_checked': files_checked,
                'lines_checked': lines_checked,
                'violations_by_severity': violations_by_severity
            },
            'results': results,
            'waiver_stats': waiver_manager.get_waiver_statistics() if waiver_manager else {}
        }
    
    def _show_header(self) -> None:
        """Show report header"""
        header_text = Text.from_markup(
            f"[bold cyan]Consistency Check Report[/bold cyan]\n"
            f"[dim]Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]"
        )
        
        header_panel = Panel(
            Align.center(header_text),
            border_style="cyan",
            expand=False
        )
        
        self.console.print("\n")
        self.console.print(header_panel)
        self.console.print("\n")
    
    def _show_rule_status_table(self, results: List[CheckResult], waiver_manager: Optional[WaiverManager] = None) -> None:
        """Show table with rule status and statistics"""
        table = Table(
            title="[bold]Rule Execution Summary[/bold]",
            show_header=True,
            header_style="bold cyan",
            border_style="blue",
            expand=True
        )
        
        table.add_column("Rule", style="bold", no_wrap=True)
        table.add_column("Status", justify="center", no_wrap=True)
        table.add_column("Violations", justify="right", style="red")
        table.add_column("Warnings", justify="right", style="yellow")
        table.add_column("Waived", justify="right", style="blue")
        table.add_column("Unused Waivers", justify="right", style="orange3")
        table.add_column("Time", justify="right", style="dim")
        table.add_column("Files", justify="right", style="dim")
        
        # Get unused waivers per rule from waiver manager if available
        unused_waivers_by_rule = {}
        if waiver_manager:
            unused_waivers_by_rule = waiver_manager.get_unused_waivers_by_rule()
        
        for result in sorted(results, key=lambda r: r.rule_name):
            # Determine status with appropriate styling
            if not result.success:
                status = "[red]ERROR[/red]"
            elif result.passed:
                status = "[green]PASS[/green]"
            else:
                status = "[red]FAIL[/red]"
            
            # Count violations by severity for this rule
            critical_count = len([v for v in result.violations if v.severity == Severity.CRITICAL])
            error_count = len([v for v in result.violations if v.severity == Severity.ERROR])
            
            # Format violations count with severity indicators
            violations_text = str(len(result.violations))
            if critical_count > 0:
                violations_text = f"[bold red]{violations_text}[/bold red]"
            if error_count > 0:
                violations_text = f"[red]{violations_text}[/red]"
            
            # Get unused waivers count for this rule
            unused_count = unused_waivers_by_rule.get(result.rule_name, 0)
            unused_text = str(unused_count) if unused_count > 0 else "-"
            if unused_count > 0:
                unused_text = f"[orange3]{unused_count}[/orange3]"
            
            table.add_row(
                result.rule_name,
                status,
                violations_text,
                str(len(result.warnings)),
                str(result.waiver_count),
                unused_text,
                f"{result.execution_time:.2f}s",
                str(result.files_checked) if result.files_checked > 0 else "-"
            )
        
        self.console.print(table)
        self.console.print()
    
    
    def _show_violation_details(self, results: List[CheckResult]) -> None:
        """Show detailed violation information"""
        results_with_violations = [r for r in results if r.violations or r.warnings]
        
        if not results_with_violations:
            self.console.print("[green]✓ No violations found![/green]\n")
            return
        
        for result in results_with_violations:
            if result.violations:
                self._show_rule_violations(result, "Violations", result.violations, "red")
            
            if result.warnings:
                self._show_rule_violations(result, "Warnings", result.warnings, "yellow")
    
    def _show_rule_violations(
        self,
        result: CheckResult,
        section_title: str,
        violations: List[Violation],
        color: str
    ) -> None:
        """Show violations for a specific rule"""
        title = f"[bold {color}]{result.rule_name} - {section_title} ({len(violations)})[/bold {color}]"
        
        # Group violations by file for better organization
        violations_by_file = {}
        for violation in violations:
            file_path = violation.file_path
            if file_path not in violations_by_file:
                violations_by_file[file_path] = []
            violations_by_file[file_path].append(violation)
        
        # Create a tree structure for violations
        tree = Tree(title, guide_style="dim")
        
        for file_path, file_violations in sorted(violations_by_file.items()):
            file_node = tree.add(f"[blue]{file_path}[/blue] ({len(file_violations)} issues)")
            
            for violation in sorted(file_violations, key=lambda v: v.line_number):
                # Create violation description
                location = f"Line {violation.line_number}"
                if violation.column > 0:
                    location += f", Column {violation.column}"
                
                severity_style = {
                    Severity.CRITICAL: "bold red",
                    Severity.ERROR: "red",
                    Severity.WARNING: "yellow",
                    Severity.INFO: "blue"
                }.get(violation.severity, "white")
                
                violation_text = f"[{severity_style}]{violation.severity.value.upper()}[/{severity_style}]: {violation.message}"
                violation_node = file_node.add(f"{location}: {violation_text}")
                
                # Add code snippet if available
                if violation.code_snippet:
                    # Truncate very long lines
                    code = violation.code_snippet.strip()
                    if len(code) > 100:
                        code = code[:97] + "..."
                    violation_node.add(f"[dim]Code: {code}[/dim]")
                
                # Add suggested fix if available
                if violation.suggested_fix:
                    violation_node.add(f"[green]Suggested fix: {violation.suggested_fix}[/green]")
        
        self.console.print(tree)
        self.console.print()
    
    def _show_waiver_summary(self, waiver_manager: WaiverManager) -> None:
        """Show waiver statistics and important information"""
        stats = waiver_manager.get_waiver_statistics()
        
        if stats['total_waivers'] == 0:
            return
        
        # Create waiver summary panel
        summary_text = Text.from_markup(
            f"[bold]Total Waivers:[/bold] {stats['total_waivers']}\n"
            f"[bold]Active Waivers:[/bold] [green]{stats['active_waivers']}[/green]\n"
            f"[bold]Expired Waivers:[/bold] [red]{stats['expired_waivers']}[/red]\n"
            f"[bold]Unused Waivers:[/bold] [yellow]{stats['unused_waivers']}[/yellow]\n"
            f"[bold]Expiring Soon:[/bold] [yellow]{stats['expiring_soon']}[/yellow]"
        )
        
        waiver_panel = Panel(
            summary_text,
            title="[bold]Waiver Summary[/bold]",
            border_style="blue",
            expand=False
        )
        
        self.console.print(waiver_panel)
        
        # Show expiring waivers warning
        expiring = waiver_manager.get_expiring_waivers()
        if expiring:
            self.console.print("\n[yellow]⚠ Waivers expiring soon:[/yellow]")
            for waiver in expiring[:5]:  # Show first 5
                days_left = waiver.days_until_expiry()
                self.console.print(f"  • {waiver.id}: expires in {days_left} days")
            
            if len(expiring) > 5:
                self.console.print(f"  ... and {len(expiring) - 5} more")
        
        self.console.print()
    
    def _show_final_summary(self) -> int:
        """Show final summary and return exit code"""
        summary = self.report_data['summary']
        
        # Determine overall status
        has_critical = summary['violations_by_severity'][Severity.CRITICAL] > 0
        has_errors = summary['violations_by_severity'][Severity.ERROR] > 0
        
        if has_critical:
            status = "[bold red]CRITICAL ISSUES FOUND[/bold red]"
            exit_code = 2
        elif has_errors:
            status = "[bold red]FAILED[/bold red]"
            exit_code = 1
        elif summary['total_violations'] > 0:
            status = "[yellow]WARNINGS ONLY[/yellow]"
            exit_code = 0
        else:
            status = "[bold green]PASSED[/bold green]"
            exit_code = 0
        
        # Create final summary
        summary_text = Text.from_markup(
            f"[bold]Rules Executed:[/bold] {summary['total_rules']}\n"
            f"[bold]Rules Passed:[/bold] [green]{summary['passed_rules']}[/green]\n"
            f"[bold]Rules Failed:[/bold] [red]{summary['failed_rules']}[/red]\n"
            f"[bold]Total Issues:[/bold] {summary['total_violations'] + summary['total_warnings']}\n"
            f"  • [red]Critical: {summary['violations_by_severity'][Severity.CRITICAL]}[/red]\n"
            f"  • [red]Errors: {summary['violations_by_severity'][Severity.ERROR]}[/red]\n"
            f"  • [yellow]Warnings: {summary['violations_by_severity'][Severity.WARNING]}[/yellow]\n"
            f"  • [blue]Info: {summary['violations_by_severity'][Severity.INFO]}[/blue]\n"
            f"[bold]Issues Waived:[/bold] [blue]{summary['total_waived']}[/blue]\n"
            f"[bold]Execution Time:[/bold] {summary['execution_time']:.2f}s\n"
            f"[bold]Files Checked:[/bold] {summary['files_checked']}\n"
            f"[bold]Status:[/bold] {status}"
        )
        
        final_panel = Panel(
            summary_text,
            title="[bold]Final Results[/bold]",
            border_style="green" if exit_code == 0 else "red",
            expand=False
        )
        
        self.console.print(final_panel)
        self.console.print()
        
        return exit_code
    
    def generate_html_report(
        self,
        results: List[CheckResult],
        output_file: Path,
        waiver_manager: Optional[WaiverManager] = None
    ) -> None:
        """Generate HTML report"""
        self._prepare_report_data(results, waiver_manager)
        
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Consistency Check Report</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid #e0e0e0; }
        .header h1 { color: #2c3e50; margin: 0; }
        .header .timestamp { color: #7f8c8d; font-size: 14px; }
        .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .summary-card { background: #f8f9fa; padding: 20px; border-radius: 6px; border-left: 4px solid #3498db; }
        .summary-card h3 { margin: 0 0 10px 0; color: #2c3e50; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; }
        .summary-card .value { font-size: 28px; font-weight: bold; color: #2c3e50; }
        .summary-card.success { border-left-color: #27ae60; }
        .summary-card.warning { border-left-color: #f39c12; }
        .summary-card.error { border-left-color: #e74c3c; }
        .rules-table { width: 100%; border-collapse: collapse; margin-bottom: 30px; }
        .rules-table th, .rules-table td { padding: 12px; text-align: left; border-bottom: 1px solid #e0e0e0; }
        .rules-table th { background: #3498db; color: white; font-weight: 600; }
        .rules-table tr:hover { background: #f8f9fa; }
        .status-pass { color: #27ae60; font-weight: bold; }
        .status-fail { color: #e74c3c; font-weight: bold; }
        .status-error { color: #e74c3c; font-weight: bold; }
        .violations-section { margin-top: 30px; }
        .violation-file { background: #f8f9fa; padding: 15px; margin-bottom: 15px; border-radius: 6px; border-left: 4px solid #e74c3c; }
        .violation-file h4 { margin: 0 0 10px 0; color: #2c3e50; }
        .violation-item { background: white; padding: 10px; margin-bottom: 8px; border-radius: 4px; border-left: 3px solid #e74c3c; }
        .violation-item.warning { border-left-color: #f39c12; }
        .violation-item.info { border-left-color: #3498db; }
        .violation-location { font-size: 12px; color: #7f8c8d; margin-bottom: 5px; }
        .violation-message { color: #2c3e50; margin-bottom: 5px; }
        .violation-code { background: #f4f4f4; padding: 8px; border-radius: 3px; font-family: monospace; font-size: 12px; margin-top: 5px; }
        .expandable { cursor: pointer; user-select: none; }
        .expandable:hover { background: #ecf0f1; }
        .expanded-content { display: none; }
        .toggle { float: right; font-size: 12px; color: #7f8c8d; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Consistency Check Report</h1>
            <div class="timestamp">Generated: {{ report_data.timestamp }}</div>
        </div>
        
        <div class="summary-grid">
            <div class="summary-card">
                <h3>Total Rules</h3>
                <div class="value">{{ report_data.summary.total_rules }}</div>
            </div>
            <div class="summary-card success">
                <h3>Rules Passed</h3>
                <div class="value">{{ report_data.summary.passed_rules }}</div>
            </div>
            <div class="summary-card error">
                <h3>Rules Failed</h3>
                <div class="value">{{ report_data.summary.failed_rules }}</div>
            </div>
            <div class="summary-card warning">
                <h3>Total Issues</h3>
                <div class="value">{{ report_data.summary.total_violations + report_data.summary.total_warnings }}</div>
            </div>
            <div class="summary-card">
                <h3>Issues Waived</h3>
                <div class="value">{{ report_data.summary.total_waived }}</div>
            </div>
        </div>
        
        <table class="rules-table">
            <thead>
                <tr>
                    <th>Rule</th>
                    <th>Status</th>
                    <th>Violations</th>
                    <th>Warnings</th>
                    <th>Waived</th>
                    <th>Time (s)</th>
                    <th>Files</th>
                </tr>
            </thead>
            <tbody>
                {% for result in report_data.results %}
                <tr>
                    <td>{{ result.rule_name }}</td>
                    <td>
                        {% if not result.success %}
                            <span class="status-error">ERROR</span>
                        {% elif result.passed %}
                            <span class="status-pass">PASS</span>
                        {% else %}
                            <span class="status-fail">FAIL</span>
                        {% endif %}
                    </td>
                    <td>{{ result.violations|length }}</td>
                    <td>{{ result.warnings|length }}</td>
                    <td>{{ result.waiver_count }}</td>
                    <td>{{ "%.2f"|format(result.execution_time) }}</td>
                    <td>{{ result.files_checked if result.files_checked > 0 else "-" }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        {% if violations_by_rule %}
        <div class="violations-section">
            <h2>Detailed Violations</h2>
            {% for rule_name, rule_violations in violations_by_rule.items() %}
                {% for file_path, file_violations in rule_violations.items() %}
                <div class="violation-file">
                    <h4 class="expandable" onclick="toggleExpand('{{ rule_name }}_{{ loop.index }}')">
                        {{ rule_name }} - {{ file_path }} ({{ file_violations|length }} issues)
                        <span class="toggle" id="toggle_{{ rule_name }}_{{ loop.index }}">▼</span>
                    </h4>
                    <div class="expanded-content" id="content_{{ rule_name }}_{{ loop.index }}">
                        {% for violation in file_violations %}
                        <div class="violation-item {{ violation.severity.value }}">
                            <div class="violation-location">
                                Line {{ violation.line_number }}{% if violation.column > 0 %}, Column {{ violation.column }}{% endif %}
                            </div>
                            <div class="violation-message">{{ violation.message }}</div>
                            {% if violation.code_snippet %}
                            <div class="violation-code">{{ violation.code_snippet }}</div>
                            {% endif %}
                        </div>
                        {% endfor %}
                    </div>
                </div>
                {% endfor %}
            {% endfor %}
        </div>
        {% endif %}
    </div>
    
    <script>
        function toggleExpand(id) {
            const content = document.getElementById('content_' + id);
            const toggle = document.getElementById('toggle_' + id);
            if (content.style.display === 'none' || content.style.display === '') {
                content.style.display = 'block';
                toggle.textContent = '▲';
            } else {
                content.style.display = 'none';
                toggle.textContent = '▼';
            }
        }
        
        // Auto-expand first few violation sections
        document.addEventListener('DOMContentLoaded', function() {
            const expandables = document.querySelectorAll('.expandable');
            for (let i = 0; i < Math.min(3, expandables.length); i++) {
                expandables[i].click();
            }
        });
    </script>
</body>
</html>
        """
        
        # Prepare violations data for template
        violations_by_rule = {}
        for result in results:
            if result.violations:
                violations_by_file = {}
                for violation in result.violations:
                    file_path = violation.file_path
                    if file_path not in violations_by_file:
                        violations_by_file[file_path] = []
                    violations_by_file[file_path].append(violation)
                violations_by_rule[result.rule_name] = violations_by_file
        
        template = Template(html_template)
        html_content = template.render(
            report_data=self.report_data,
            violations_by_rule=violations_by_rule
        )
        
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        self.console.print(f"[green]HTML report generated: {output_file}[/green]")
    
    def generate_json_report(
        self,
        results: List[CheckResult],
        output_file: Path,
        waiver_manager: Optional[WaiverManager] = None
    ) -> None:
        """Generate JSON report for CI/CD integration"""
        self._prepare_report_data(results, waiver_manager)
        
        # Convert results to JSON-serializable format
        json_results = []
        for result in results:
            json_result = {
                'rule_name': result.rule_name,
                'success': result.success,
                'passed': result.passed,
                'execution_time': result.execution_time,
                'files_checked': result.files_checked,
                'lines_checked': result.lines_checked,
                'violations': [asdict(v) for v in result.violations],
                'warnings': [asdict(v) for v in result.warnings],
                'waiver_count': result.waiver_count,
                'waived_violations': [asdict(v) for v in result.waived_violations]
            }
            
            json_results.append(json_result)
        
        report_json = {
            'metadata': {
                'timestamp': self.report_data['timestamp'],
                'format_version': '1.0'
            },
            'summary': self.report_data['summary'],
            'results': json_results,
            'waiver_stats': self.report_data['waiver_stats']
        }
        
        with open(output_file, 'w') as f:
            json.dump(report_json, f, indent=2, default=str)
        
        self.console.print(f"[green]JSON report generated: {output_file}[/green]")
    
    def generate_csv_report(
        self,
        results: List[CheckResult],
        output_file: Path
    ) -> None:
        """Generate CSV report for data analysis"""
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = [
                'rule_name', 'file_path', 'line_number', 'column',
                'severity', 'message', 'code_snippet', 'category'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                for violation in result.violations + result.warnings:
                    writer.writerow({
                        'rule_name': violation.rule_name,
                        'file_path': violation.file_path,
                        'line_number': violation.line_number,
                        'column': violation.column,
                        'severity': violation.severity.value,
                        'message': violation.message,
                        'code_snippet': violation.code_snippet,
                        'category': violation.rule_category
                    })
        
        self.console.print(f"[green]CSV report generated: {output_file}[/green]")
