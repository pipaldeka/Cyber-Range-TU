"""
Event Queue System
High-performance async queue for event processing
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, List
from collections import deque
import json

logger = logging.getLogger(__name__)

class EventQueue:
    def __init__(self, config: Dict):
        self.config = config
        self.queue = asyncio.Queue(maxsize=config['queue']['max_size'])
        self.batch_size = config['queue']['batch_size']
        self.flush_interval = config['queue']['flush_interval']
        self.processing = True
        
        # Statistics
        self.stats = {
            'events_received': 0,
            'events_processed': 0,
            'events_dropped': 0,
            'batches_processed': 0
        }
    
    async def put(self, event: Dict):
        """Add event to queue"""
        try:
            await self.queue.put(event)
            self.stats['events_received'] += 1
        except asyncio.QueueFull:
            logger.warning("Queue full, dropping event")
            self.stats['events_dropped'] += 1
    
    async def get(self) -> Optional[Dict]:
        """Get single event from queue"""
        try:
            event = await asyncio.wait_for(self.queue.get(), timeout=1.0)
            return event
        except asyncio.TimeoutError:
            return None
    
    async def get_batch(self) -> List[Dict]:
        """Get batch of events from queue"""
        batch = []
        
        try:
            # Get first event (with timeout)
            first_event = await asyncio.wait_for(
                self.queue.get(), 
                timeout=self.flush_interval
            )
            batch.append(first_event)
            
            # Get remaining events (non-blocking)
            while len(batch) < self.batch_size and not self.queue.empty():
                try:
                    event = self.queue.get_nowait()
                    batch.append(event)
                except asyncio.QueueEmpty:
                    break
            
            self.stats['batches_processed'] += 1
            self.stats['events_processed'] += len(batch)
            
        except asyncio.TimeoutError:
            # Return empty batch on timeout
            pass
        
        return batch
    
    def get_stats(self) -> Dict:
        """Get queue statistics"""
        return {
            **self.stats,
            'queue_size': self.queue.qsize(),
            'queue_capacity': self.queue.maxsize
        }
    
    async def clear(self):
        """Clear the queue"""
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        logger.info("Queue cleared")

