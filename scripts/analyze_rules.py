#!/usr/bin/env python3
"""
Script to analyze rules.py and categorize rules by vertical

This script:
1. Parses rules.py
2. Extracts all rule classes
3. Categorizes them by primary vertical
4. Outputs categorization for migration
"""

import re
from pathlib import Path

def analyze_rules():
    rules_file = Path("/home/user/sentinel/app/services/rules.py")
    content = rules_file.read_text()

    # Find all rule class definitions
    rule_pattern = r'class\s+(\w+Rule)\(FraudRule\):(.*?)(?=class\s+\w+Rule\(FraudRule\):|class\s+FraudRulesEngine:|$)'

    rules = {}
    matches = re.finditer(rule_pattern, content, re.DOTALL)

    for match in matches:
        rule_name = match.group(1)
        rule_body = match.group(2)

        # Extract verticals
        verticals_match = re.search(r'verticals\s*=\s*\[(.*?)\]', rule_body)
        if verticals_match:
            verticals_str = verticals_match.group(1)
            verticals = [v.strip(' "\'') for v in verticals_str.split(',')]
        else:
            verticals = ['all']

        # Extract description
        desc_match = re.search(r'description\s*=\s*["\']([^"\']+)["\']', rule_body)
        description = desc_match.group(1) if desc_match else ""

        rules[rule_name] = {
            'verticals': verticals,
            'description': description,
            'body': match.group(0)
        }

    # Categorize rules
    categories = {
        'lending': [],
        'fintech': [],
        'crypto': [],
        'ecommerce': [],
        'betting': [],
        'gaming': [],
        'marketplace': [],
        'universal': [],
        'identity': [],
        'device': [],
        'network': [],
        'behavioral': [],
        'ato': []
    }

    # Keywords for categorization
    identity_keywords = ['email', 'phone', 'bvn', 'kyc', 'verification']
    device_keywords = ['device', 'fingerprint', 'browser', 'emulator', 'jailbreak']
    network_keywords = ['ip', 'vpn', 'proxy', 'tor', 'asn', 'isp']
    behavioral_keywords = ['mouse', 'typing', 'keystroke', 'session', 'behavioral']
    ato_keywords = ['ato', 'takeover', 'password', 'login', 'hijack']

    for rule_name, data in rules.items():
        verticals = data['verticals']
        desc_lower = data['description'].lower()
        name_lower = rule_name.lower()

        # Determine primary category
        if any(kw in name_lower or kw in desc_lower for kw in identity_keywords):
            categories['identity'].append(rule_name)
        elif any(kw in name_lower or kw in desc_lower for kw in device_keywords):
            categories['device'].append(rule_name)
        elif any(kw in name_lower or kw in desc_lower for kw in network_keywords):
            categories['network'].append(rule_name)
        elif any(kw in name_lower or kw in desc_lower for kw in behavioral_keywords):
            categories['behavioral'].append(rule_name)
        elif any(kw in name_lower or kw in desc_lower for kw in ato_keywords):
            categories['ato'].append(rule_name)
        elif 'lending' in verticals or 'loan' in name_lower:
            categories['lending'].append(rule_name)
        elif 'crypto' in verticals and len(verticals) <= 3:
            categories['crypto'].append(rule_name)
        elif 'betting' in verticals and len(verticals) <= 3:
            categories['betting'].append(rule_name)
        elif 'gaming' in verticals and len(verticals) <= 3:
            categories['gaming'].append(rule_name)
        elif 'ecommerce' in verticals and len(verticals) <= 3:
            categories['ecommerce'].append(rule_name)
        elif 'marketplace' in verticals and len(verticals) <= 3:
            categories['marketplace'].append(rule_name)
        elif 'fintech' in verticals or 'payments' in verticals:
            if len(verticals) <= 3:
                categories['fintech'].append(rule_name)
            else:
                categories['universal'].append(rule_name)
        else:
            categories['universal'].append(rule_name)

    # Print categorization
    print("RULE CATEGORIZATION")
    print("=" * 80)
    for category, rule_list in categories.items():
        print(f"\n{category.upper()} ({len(rule_list)} rules):")
        for rule in rule_list:
            print(f"  - {rule}")

    print(f"\n\nTOTAL RULES: {len(rules)}")

    return rules, categories

if __name__ == "__main__":
    analyze_rules()
