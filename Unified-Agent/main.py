"""
Unified AI Agent - Main Entry Point
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
import yaml
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.docker_collector import DockerCollector
from core.event_queue import EventQueue
from core.database import Database
from detection.detector import ThreatDetector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'agent_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

logger = logging.getLogger(__name__)

class UnifiedAgent:
    def __init__(self, config_path: str = 'config/config.yaml'):
        logger.info("Initializing Unified AI Agent...")
        
        # Load configuration
        self.config = self.load_config(config_path)
        
        # Initialize components
        self.event_queue = EventQueue(self.config)
        self.database = Database(self.config)
        self.docker_collector = DockerCollector(self.config)
        self.detector = ThreatDetector(self.config)
        
        # State
        self.running = False
        self.tasks = []
    
    def load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Replace environment variables
            config = self._replace_env_vars(config)
            
            logger.info(f"Configuration loaded from {config_path}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            sys.exit(1)
    
    def _replace_env_vars(self, config: dict) -> dict:
        """Replace ${VAR} with environment variables"""
        import re
        
        def replace_value(value):
            if isinstance(value, str):
                # Find ${VAR} patterns
                pattern = r'\$\{([^}]+)\}'
                matches = re.findall(pattern, value)
                for var in matches:
                    env_value = os.getenv(var, '')
                    value = value.replace(f'${{{var}}}', env_value)
                return value
            elif isinstance(value, dict):
                return {k: replace_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [replace_value(item) for item in value]
            else:
                return value
        
        return replace_value(config)
    
    async def process_events(self):
        """Process events from queue"""
        logger.info("Starting event processor...")
        
        while self.running:
            try:
                # Get batch of events
                batch = await self.event_queue.get_batch()
                
                if not batch:
                    continue
                
                logger.debug(f"Processing batch of {len(batch)} events")
                
                for event in batch:
                    await self.process_single_event(event)
                
            except Exception as e:
                logger.error(f"Error processing events: {e}")
                await asyncio.sleep(1)
    
    async def process_single_event(self, event: dict):
        """Process a single event"""
        try:
            detections = []
            
            # Analyze based on event type
            if event['type'] == 'log':
                detections = self.detector.analyze_log(event)
            elif event['type'] == 'stats':
                detections = self.detector.analyze_stats(event)
            
            # Store event in database
            self.database.insert_event({
                'timestamp': event['timestamp'],
                'student_id': event['student_id'],
                'container_name': event['container_name'],
                'service': event.get('service'),
                'event_type': event['type'],
                'severity': 'INFO',
                'technique': None,
                'data': event
            })
            
            # Process detections
            for detection in detections:
                await self.handle_detection(detection)
            
        except Exception as e:
            logger.error(f"Error processing event: {e}")
    
    async def handle_detection(self, detection: dict):
        """Handle a detection"""
        try:
            detection_type = detection['type']
            event = detection['event']
            
            if detection_type == 'exploit':
                # Critical exploit detected
                logger.warning(
                    f"🚨 EXPLOIT: {detection['name']} - "
                    f"Student: {event['student_id']} - "
                    f"Severity: {detection['severity']}"
                )
                
                # Generate alert
                self.database.insert_alert({
                    'timestamp': event['timestamp'],
                    'student_id': event['student_id'],
                    'container_name': event['container_name'],
                    'alert_type': detection['name'],
                    'severity': detection['severity'],
                    'technique': detection.get('technique'),
                    'description': detection.get('description'),
                    'response_action': 'LOGGED',
                    'evidence': {
                        'context': detection.get('context'),
                        'log': event.get('log', '')[:500]
                    }
                })
                
                # Award points for exploit
                if detection.get('points', 0) > 0:
                    self.database.insert_score({
                        'timestamp': event['timestamp'],
                        'student_id': event['student_id'],
                        'event_type': 'EXPLOIT',
                        'points': detection['points'],
                        'technique': detection.get('technique'),
                        'quality_score': 1.0,
                        'multiplier': 1.0
                    })
                    
                    logger.info(
                        f"💯 POINTS: {event['student_id']} earned "
                        f"{detection['points']} points for {detection['name']}"
                    )
            
            elif detection_type == 'flag':
                # Flag captured!
                logger.info(
                    f"🚩 FLAG: {event['student_id']} captured "
                    f"{detection['flag']}"
                )
                
                # Insert flag
                flag_id, is_first_blood = self.database.insert_flag({
                    'timestamp': event['timestamp'],
                    'student_id': event['student_id'],
                    'container_name': event['container_name'],
                    'service': event.get('service'),
                    'flag': detection['flag'],
                    'method': detection.get('method'),
                    'time_taken': 0
                })
                
                if flag_id:
                    # Award points
                    points = detection.get('points', 200)
                    multiplier = 2.0 if is_first_blood else 1.0
                    
                    self.database.insert_score({
                        'timestamp': event['timestamp'],
                        'student_id': event['student_id'],
                        'event_type': 'FLAG_CAPTURE',
                        'points': int(points * multiplier),
                        'technique': 'FLAG_CAPTURE',
                        'quality_score': 1.0,
                        'multiplier': multiplier
                    })
                    
                    if is_first_blood:
                        logger.info(f"🩸 FIRST BLOOD! {event['student_id']}")
            
            elif detection_type == 'anomaly':
                # Anomaly detected
                logger.warning(
                    f"⚠️  ANOMALY: {detection['name']} - "
                    f"Student: {event['student_id']} - "
                    f"Value: {detection['value']}"
                )
                
                # Generate alert
                self.database.insert_alert({
                    'timestamp': event['timestamp'],
                    'student_id': event['student_id'],
                    'container_name': event['container_name'],
                    'alert_type': detection['name'],
                    'severity': detection['severity'],
                    'technique': detection.get('technique'),
                    'description': detection['description'],
                    'response_action': 'MONITORED',
                    'evidence': {'stats': event.get('stats', {})}
                })
            
            elif detection_type == 'suspicious':
                # Suspicious activity
                logger.info(
                    f"🔍 SUSPICIOUS: {detection['name']} - "
                    f"Student: {event['student_id']}"
                )
                
                # Log as alert
                self.database.insert_alert({
                    'timestamp': event['timestamp'],
                    'student_id': event['student_id'],
                    'container_name': event['container_name'],
                    'alert_type': detection['name'],
                    'severity': detection['severity'],
                    'technique': detection.get('technique'),
                    'description': detection.get('description'),
                    'response_action': 'LOGGED',
                    'evidence': {'context': detection.get('context')}
                })
        
        except Exception as e:
            logger.error(f"Error handling detection: {e}")
    
    async def print_stats(self):
        """Print statistics periodically"""
        while self.running:
            await asyncio.sleep(30)  # Every 30 seconds
            
            try:
                queue_stats = self.event_queue.get_stats()
                leaderboard = self.database.get_leaderboard(limit=5)
                
                logger.info("=" * 60)
                logger.info("📊 AGENT STATISTICS")
                logger.info("=" * 60)
                logger.info(f"Queue Size: {queue_stats['queue_size']}/{queue_stats['queue_capacity']}")
                logger.info(f"Events Received: {queue_stats['events_received']}")
                logger.info(f"Events Processed: {queue_stats['events_processed']}")
                logger.info(f"Events Dropped: {queue_stats['events_dropped']}")
                logger.info(f"Batches Processed: {queue_stats['batches_processed']}")
                
                if leaderboard:
                    logger.info("\n🏆 TOP 5 LEADERBOARD:")
                    for i, entry in enumerate(leaderboard, 1):
                        logger.info(
                            f"  {i}. {entry['student_id']}: "
                            f"{entry['total_score']} points "
                            f"({entry['flags_captured']} flags)"
                        )
                
                logger.info("=" * 60)
                
            except Exception as e:
                logger.error(f"Error printing stats: {e}")
    
    async def start(self):
        """Start the agent"""
        logger.info("🚀 Starting Unified AI Agent")
        logger.info(f"Version: {self.config['agent']['version']}")
        self.running = True
        
        # Create tasks
        self.tasks = [
            asyncio.create_task(self.docker_collector.start_monitoring(self.event_queue)),
            asyncio.create_task(self.process_events()),
            asyncio.create_task(self.print_stats())
        ]
        
        logger.info("✅ Agent running")
        
        # Wait for all tasks
        try:
            await asyncio.gather(*self.tasks)
        except asyncio.CancelledError:
            logger.info("Tasks cancelled")
    
    async def stop(self):
        """Stop the agent"""
        logger.info("🛑 Stopping Unified AI Agent...")
        self.running = False
        self.docker_collector.stop_monitoring()
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Close database
        self.database.close()
        
        logger.info("Agent stopped")

def signal_handler(agent):
    """Handle shutdown signals"""
    def handler(signum, frame):
        logger.info(f"Received signal {signum}")
        asyncio.create_task(agent.stop())
    return handler

async def main():
    """Main entry point"""
    # Create agent
    agent = UnifiedAgent()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler(agent))
    signal.signal(signal.SIGTERM, signal_handler(agent))
    
    # Start agent
    try:
        await agent.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        await agent.stop()

if __name__ == '__main__':
    asyncio.run(main())

