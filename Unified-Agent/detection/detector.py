"""
Threat Detection Engine
Real-time pattern matching and anomaly detection
"""

import logging
import re
from typing import Dict, List, Optional
from datetime import datetime
from detection.patterns import PatternLoader

logger = logging.getLogger(__name__)

class ThreatDetector:
    def __init__(self, config: Dict):
        self.config = config
        self.pattern_loader = PatternLoader(config['detection']['rules_file'])
        self.confidence_threshold = config['detection']['confidence_threshold']
        
        # Baseline tracking for anomaly detection
        self.baselines = {}
    
    def analyze_log(self, event: Dict) -> List[Dict]:
        """Analyze log event for threats"""
        detections = []
        log_text = event.get('log', '')
        
        if not log_text:
            return detections
        
        # Check exploit patterns
        detections.extend(self._check_exploits(event, log_text))
        
        # Check suspicious commands
        detections.extend(self._check_suspicious(event, log_text))
        
        # Check for flags
        detections.extend(self._check_flags(event, log_text))
        
        return detections
    
    def analyze_stats(self, event: Dict) -> List[Dict]:
        """Analyze stats event for anomalies"""
        detections = []
        stats = event.get('stats', {})
        student_id = event['student_id']
        container = event['container_name']
        
        # Get or create baseline
        baseline_key = f"{student_id}_{container}"
        if baseline_key not in self.baselines:
            self.baselines[baseline_key] = {
                'cpu_history': [],
                'memory_history': [],
                'network_rx_history': [],
                'network_tx_history': []
            }
        
        baseline = self.baselines[baseline_key]
        thresholds = self.pattern_loader.get_anomaly_thresholds()
        
        # CPU anomaly
        cpu_percent = stats.get('cpu_percent', 0)
        if cpu_percent > thresholds.get('cpu_percent', 90):
            detections.append({
                'type': 'anomaly',
                'name': 'HIGH_CPU_USAGE',
                'severity': 'MEDIUM',
                'description': f"CPU usage at {cpu_percent:.1f}%",
                'value': cpu_percent,
                'threshold': thresholds.get('cpu_percent'),
                'event': event
            })
        
        # Memory anomaly
        memory_percent = stats.get('memory_percent', 0)
        if memory_percent > thresholds.get('memory_percent', 90):
            detections.append({
                'type': 'anomaly',
                'name': 'HIGH_MEMORY_USAGE',
                'severity': 'MEDIUM',
                'description': f"Memory usage at {memory_percent:.1f}%",
                'value': memory_percent,
                'threshold': thresholds.get('memory_percent'),
                'event': event
            })
        
        # Network anomaly (large transfers)
        network_tx = stats.get('network_tx_bytes', 0) / (1024 * 1024)  # MB
        if network_tx > thresholds.get('network_tx_mb', 100):
            detections.append({
                'type': 'anomaly',
                'name': 'HIGH_NETWORK_TX',
                'severity': 'HIGH',
                'description': f"High network transmission: {network_tx:.2f} MB",
                'technique': 'T1041',  # Exfiltration Over C2 Channel
                'value': network_tx,
                'threshold': thresholds.get('network_tx_mb'),
                'event': event
            })
        
        # Update baseline history (keep last 100 samples)
        baseline['cpu_history'].append(cpu_percent)
        baseline['memory_history'].append(memory_percent)
        baseline['network_tx_history'].append(network_tx)
        
        for key in baseline:
            if len(baseline[key]) > 100:
                baseline[key] = baseline[key][-100:]
        
        return detections
    
    def _check_exploits(self, event: Dict, log_text: str) -> List[Dict]:
        """Check for exploit patterns"""
        detections = []
        
        for rule in self.pattern_loader.get_exploit_patterns():
            if rule['pattern'].search(log_text):
                # Extract context around match
                context = self._extract_context(log_text, rule['pattern'])
                
                detection = {
                    'type': 'exploit',
                    'name': rule['name'],
                    'severity': rule['severity'],
                    'technique': rule.get('technique'),
                    'description': rule.get('description'),
                    'points': rule.get('points', 0),
                    'context': context,
                    'event': event
                }
                
                detections.append(detection)
                
                logger.info(f"Exploit detected: {rule['name']} for {event['student_id']}")
        
        return detections
    
    def _check_suspicious(self, event: Dict, log_text: str) -> List[Dict]:
        """Check for suspicious command patterns"""
        detections = []
        
        for rule in self.pattern_loader.get_suspicious_patterns():
            if rule['pattern'].search(log_text):
                context = self._extract_context(log_text, rule['pattern'])
                
                detection = {
                    'type': 'suspicious',
                    'name': rule['name'],
                    'severity': rule['severity'],
                    'technique': rule.get('technique'),
                    'description': rule.get('description'),
                    'context': context,
                    'event': event
                }
                
                detections.append(detection)
                
                logger.debug(f"Suspicious activity: {rule['name']} for {event['student_id']}")
        
        return detections
    
    def _check_flags(self, event: Dict, log_text: str) -> List[Dict]:
        """Check for flag captures"""
        detections = []
        
        for rule in self.pattern_loader.get_flag_patterns():
            matches = rule['pattern'].findall(log_text)
            
            for flag in matches:
                detection = {
                    'type': 'flag',
                    'name': rule['name'],
                    'flag': flag,
                    'points': rule.get('points', 200),
                    'method': self._determine_capture_method(log_text),
                    'event': event
                }
                
                detections.append(detection)
                
                logger.info(f"Flag captured: {flag} by {event['student_id']}")
        
        return detections
    
    def _extract_context(self, text: str, pattern: re.Pattern, lines: int = 2) -> str:
        """Extract context around pattern match"""
        try:
            match = pattern.search(text)
            if not match:
                return text[:200]
            
            # Get position of match
            start = match.start()
            end = match.end()
            
            # Extend to include surrounding lines
            context_start = max(0, start - 100)
            context_end = min(len(text), end + 100)
            
            return text[context_start:context_end]
            
        except Exception as e:
            logger.error(f"Error extracting context: {e}")
            return text[:200]
    
    def _determine_capture_method(self, log_text: str) -> str:
        """Determine how flag was captured"""
        text_lower = log_text.lower()
        
        if 'curl' in text_lower or 'wget' in text_lower:
            return 'HTTP_REQUEST'
        elif 'cat' in text_lower:
            return 'FILE_READ'
        elif 'echo' in text_lower or 'printenv' in text_lower:
            return 'ENV_VAR'
        elif 'grep' in text_lower:
            return 'FILE_SEARCH'
        else:
            return 'UNKNOWN'
    
    def get_baseline(self, student_id: str, container: str) -> Optional[Dict]:
        """Get baseline for student/container"""
        key = f"{student_id}_{container}"
        return self.baselines.get(key)

