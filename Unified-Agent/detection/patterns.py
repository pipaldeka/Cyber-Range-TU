"""
Pattern and Rules Loader
Load detection rules from YAML configuration
"""

import yaml
import re
import logging
from typing import Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)

class PatternLoader:
    def __init__(self, rules_file: str):
        self.rules_file = Path(rules_file)
        self.rules = self.load_rules()
        self.compiled_patterns = self.compile_patterns()
    
    def load_rules(self) -> Dict:
        """Load rules from YAML file"""
        try:
            with open(self.rules_file, 'r') as f:
                rules = yaml.safe_load(f)
            
            logger.info(f"Loaded detection rules from {self.rules_file}")
            return rules
            
        except Exception as e:
            logger.error(f"Failed to load rules: {e}")
            return self.default_rules()
    
    def default_rules(self) -> Dict:
        """Return default rules if file loading fails"""
        return {
            'exploit_patterns': [],
            'suspicious_commands': [],
            'flag_patterns': [],
            'anomaly_thresholds': {}
        }
    
    def compile_patterns(self) -> Dict:
        """Compile regex patterns for performance"""
        compiled = {
            'exploit': [],
            'suspicious': [],
            'flag': []
        }
        
        # Compile exploit patterns
        for rule in self.rules.get('exploit_patterns', []):
            try:
                compiled['exploit'].append({
                    'name': rule['name'],
                    'pattern': re.compile(rule['pattern'], re.IGNORECASE),
                    'severity': rule['severity'],
                    'technique': rule.get('technique'),
                    'description': rule.get('description'),
                    'points': rule.get('points', 0)
                })
            except re.error as e:
                logger.error(f"Invalid regex in rule {rule['name']}: {e}")
        
        # Compile suspicious command patterns
        for rule in self.rules.get('suspicious_commands', []):
            try:
                compiled['suspicious'].append({
                    'name': rule['name'],
                    'pattern': re.compile(rule['pattern'], re.IGNORECASE),
                    'severity': rule['severity'],
                    'technique': rule.get('technique'),
                    'description': rule.get('description')
                })
            except re.error as e:
                logger.error(f"Invalid regex in rule {rule['name']}: {e}")
        
        # Compile flag patterns
        for rule in self.rules.get('flag_patterns', []):
            try:
                compiled['flag'].append({
                    'name': rule['name'],
                    'pattern': re.compile(rule['pattern']),
                    'points': rule.get('points', 0)
                })
            except re.error as e:
                logger.error(f"Invalid regex in rule {rule['name']}: {e}")
        
        logger.info(f"Compiled {len(compiled['exploit'])} exploit patterns")
        logger.info(f"Compiled {len(compiled['suspicious'])} suspicious patterns")
        logger.info(f"Compiled {len(compiled['flag'])} flag patterns")
        
        return compiled
    
    def get_exploit_patterns(self) -> List[Dict]:
        """Get compiled exploit patterns"""
        return self.compiled_patterns['exploit']
    
    def get_suspicious_patterns(self) -> List[Dict]:
        """Get compiled suspicious command patterns"""
        return self.compiled_patterns['suspicious']
    
    def get_flag_patterns(self) -> List[Dict]:
        """Get compiled flag patterns"""
        return self.compiled_patterns['flag']
    
    def get_anomaly_thresholds(self) -> Dict:
        """Get anomaly detection thresholds"""
        return self.rules.get('anomaly_thresholds', {})
    
    def reload(self):
        """Reload rules from file"""
        logger.info("Reloading detection rules...")
        self.rules = self.load_rules()
        self.compiled_patterns = self.compile_patterns()

