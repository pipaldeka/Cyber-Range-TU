"""
Docker Log and Stats Collector
Real-time streaming from Docker API
"""

import docker
import asyncio
import logging
from datetime import datetime
from typing import Dict, AsyncGenerator, Optional
import json

logger = logging.getLogger(__name__)

class DockerCollector:
    def __init__(self, config: Dict):
        self.config = config
        self.client = docker.from_env()
        self.monitoring = True
        
    def get_monitored_containers(self):
        """Get containers to monitor based on network filter"""
        containers = []
        network_filter = self.config['docker']['monitor_networks']
        
        for container in self.client.containers.list():
            # Check if container is in monitored networks
            networks = container.attrs['NetworkSettings']['Networks'].keys()
            
            for net in networks:
                for filter_pattern in network_filter:
                    if filter_pattern.replace('*', '') in net:
                        containers.append(container)
                        break
        
        logger.info(f"Monitoring {len(containers)} containers")
        return containers
    
    async def stream_logs(self, container, event_queue):
        """Stream logs from a container"""
        student_id = self.extract_student_id(container.name)
        
        try:
            for log_line in container.logs(stream=True, follow=True):
                if not self.monitoring:
                    break
                
                try:
                    log_text = log_line.decode('utf-8', errors='ignore').strip()
                    
                    if not log_text:
                        continue
                    
                    event = {
                        'type': 'log',
                        'timestamp': datetime.utcnow().isoformat(),
                        'container_id': container.id[:12],
                        'container_name': container.name,
                        'student_id': student_id,
                        'service': self.extract_service_name(container.name),
                        'log': log_text,
                        'raw': log_line
                    }
                    
                    await event_queue.put(event)
                    
                except Exception as e:
                    logger.error(f"Error processing log line: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error streaming logs from {container.name}: {e}")
    
    async def stream_stats(self, container, event_queue):
        """Stream stats from a container"""
        student_id = self.extract_student_id(container.name)
        interval = self.config['docker']['stats_interval']
        
        try:
            for stats in container.stats(stream=True, decode=True):
                if not self.monitoring:
                    break
                
                try:
                    cpu_percent = self.calculate_cpu_percent(stats)
                    memory_usage = stats['memory_stats'].get('usage', 0)
                    memory_limit = stats['memory_stats'].get('limit', 1)
                    memory_percent = (memory_usage / memory_limit) * 100 if memory_limit > 0 else 0
                    
                    networks = stats.get('networks', {})
                    network_rx = sum(net.get('rx_bytes', 0) for net in networks.values())
                    network_tx = sum(net.get('tx_bytes', 0) for net in networks.values())
                    
                    event = {
                        'type': 'stats',
                        'timestamp': datetime.utcnow().isoformat(),
                        'container_id': container.id[:12],
                        'container_name': container.name,
                        'student_id': student_id,
                        'service': self.extract_service_name(container.name),
                        'stats': {
                            'cpu_percent': round(cpu_percent, 2),
                            'memory_usage': memory_usage,
                            'memory_percent': round(memory_percent, 2),
                            'network_rx_bytes': network_rx,
                            'network_tx_bytes': network_tx
                        }
                    }
                    
                    await event_queue.put(event)
                    
                    # Sleep before next stats collection
                    await asyncio.sleep(interval)
                    
                except Exception as e:
                    logger.error(f"Error processing stats: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error streaming stats from {container.name}: {e}")
    
    def calculate_cpu_percent(self, stats: Dict) -> float:
        """Calculate CPU percentage from Docker stats"""
        try:
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            
            if system_delta > 0 and cpu_delta > 0:
                cpu_count = stats['cpu_stats'].get('online_cpus', 1)
                return (cpu_delta / system_delta) * cpu_count * 100.0
        except (KeyError, ZeroDivisionError):
            pass
        
        return 0.0
    
    def extract_student_id(self, container_name: str) -> str:
        """Extract student ID from container name (format: service-studentid)"""
        parts = container_name.rsplit('-', 1)
        return parts[1] if len(parts) == 2 else "unknown"
    
    def extract_service_name(self, container_name: str) -> str:
        """Extract service name from container name"""
        parts = container_name.rsplit('-', 1)
        return parts[0] if len(parts) == 2 else container_name
    
    async def start_monitoring(self, event_queue):
        """Start monitoring all containers"""
        logger.info("Starting Docker monitoring...")
        
        containers = self.get_monitored_containers()
        
        # Create tasks for each container
        tasks = []
        for container in containers:
            # Log streaming task
            tasks.append(asyncio.create_task(
                self.stream_logs(container, event_queue)
            ))
            
            # Stats streaming task
            tasks.append(asyncio.create_task(
                self.stream_stats(container, event_queue)
            ))
        
        logger.info(f"Started {len(tasks)} monitoring tasks")
        
        # Wait for all tasks
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error in monitoring tasks: {e}")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        logger.info("Stopping Docker monitoring...")
        self.monitoring = False

