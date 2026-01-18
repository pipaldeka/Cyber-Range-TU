"""
Database Interface
PostgreSQL connection and operations
"""

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, config: Dict):
        self.config = config['database']
        self.pool = None
        self.init_pool()
        self.init_schema()
    
    def init_pool(self):
        """Initialize connection pool"""
        try:
            self.pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=self.config['pool_size'],
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password']
            )
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    def get_connection(self):
        """Get connection from pool"""
        return self.pool.getconn()
    
    def release_connection(self, conn):
        """Release connection back to pool"""
        self.pool.putconn(conn)
    
    def init_schema(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    student_id VARCHAR(100) NOT NULL,
                    container_name VARCHAR(200) NOT NULL,
                    service VARCHAR(100),
                    event_type VARCHAR(50) NOT NULL,
                    severity VARCHAR(20),
                    technique VARCHAR(100),
                    data JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create index on timestamp and student_id
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_events_timestamp 
                ON events(timestamp DESC)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_events_student 
                ON events(student_id, timestamp DESC)
            ''')
            
            # Alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    student_id VARCHAR(100) NOT NULL,
                    container_name VARCHAR(200) NOT NULL,
                    alert_type VARCHAR(100) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    technique VARCHAR(100),
                    description TEXT,
                    response_action VARCHAR(100),
                    evidence JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_alerts_student 
                ON alerts(student_id, timestamp DESC)
            ''')
            
            # Scores table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scores (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    student_id VARCHAR(100) NOT NULL,
                    event_type VARCHAR(100),
                    points INTEGER NOT NULL,
                    technique VARCHAR(100),
                    quality_score REAL,
                    multiplier REAL DEFAULT 1.0,
                    cumulative_score INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_scores_student 
                ON scores(student_id, timestamp DESC)
            ''')
            
            # Flags table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS flags (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    student_id VARCHAR(100) NOT NULL,
                    container_name VARCHAR(200) NOT NULL,
                    service VARCHAR(100),
                    flag VARCHAR(500) NOT NULL,
                    method VARCHAR(100),
                    time_taken INTEGER,
                    first_blood BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(student_id, flag)
                )
            ''')
            
            # Student leaderboard view
            cursor.execute('''
                CREATE OR REPLACE VIEW leaderboard AS
                SELECT 
                    student_id,
                    COALESCE(SUM(points), 0) as total_score,
                    COUNT(DISTINCT CASE WHEN event_type = 'FLAG_CAPTURE' THEN id END) as flags_captured,
                    COUNT(*) as total_events,
                    MAX(timestamp) as last_activity
                FROM scores
                GROUP BY student_id
                ORDER BY total_score DESC, last_activity DESC
            ''')
            
            conn.commit()
            logger.info("Database schema initialized")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to initialize schema: {e}")
            raise
        finally:
            cursor.close()
            self.release_connection(conn)
    
    def insert_event(self, event: Dict):
        """Insert event into database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO events (
                    timestamp, student_id, container_name, service,
                    event_type, severity, technique, data
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                event.get('timestamp'),
                event.get('student_id'),
                event.get('container_name'),
                event.get('service'),
                event.get('event_type'),
                event.get('severity'),
                event.get('technique'),
                json.dumps(event.get('data', {}))
            ))
            
            event_id = cursor.fetchone()[0]
            conn.commit()
            return event_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to insert event: {e}")
            return None
        finally:
            cursor.close()
            self.release_connection(conn)
    
    def insert_alert(self, alert: Dict):
        """Insert alert into database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO alerts (
                    timestamp, student_id, container_name, alert_type,
                    severity, technique, description, response_action, evidence
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                alert.get('timestamp'),
                alert.get('student_id'),
                alert.get('container_name'),
                alert.get('alert_type'),
                alert.get('severity'),
                alert.get('technique'),
                alert.get('description'),
                alert.get('response_action'),
                json.dumps(alert.get('evidence', {}))
            ))
            
            alert_id = cursor.fetchone()[0]
            conn.commit()
            return alert_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to insert alert: {e}")
            return None
        finally:
            cursor.close()
            self.release_connection(conn)
    
    def insert_score(self, score: Dict):
        """Insert score into database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get current cumulative score
            cursor.execute('''
                SELECT COALESCE(SUM(points), 0)
                FROM scores
                WHERE student_id = %s
            ''', (score['student_id'],))
            
            current_total = cursor.fetchone()[0]
            new_total = current_total + score['points']
            
            cursor.execute('''
                INSERT INTO scores (
                    timestamp, student_id, event_type, points,
                    technique, quality_score, multiplier, cumulative_score
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                score.get('timestamp'),
                score['student_id'],
                score.get('event_type'),
                score['points'],
                score.get('technique'),
                score.get('quality_score', 1.0),
                score.get('multiplier', 1.0),
                new_total
            ))
            
            score_id = cursor.fetchone()[0]
            conn.commit()
            return score_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to insert score: {e}")
            return None
        finally:
            cursor.close()
            self.release_connection(conn)
    
    def insert_flag(self, flag: Dict):
        """Insert flag capture into database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if this is first blood
            cursor.execute('''
                SELECT COUNT(*) FROM flags WHERE flag = %s
            ''', (flag['flag'],))
            
            is_first_blood = cursor.fetchone()[0] == 0
            
            cursor.execute('''
                INSERT INTO flags (
                    timestamp, student_id, container_name, service,
                    flag, method, time_taken, first_blood
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (student_id, flag) DO NOTHING
                RETURNING id
            ''', (
                flag.get('timestamp'),
                flag['student_id'],
                flag['container_name'],
                flag.get('service'),
                flag['flag'],
                flag.get('method'),
                flag.get('time_taken', 0),
                is_first_blood
            ))
            
            result = cursor.fetchone()
            if result:
                flag_id = result[0]
                conn.commit()
                return flag_id, is_first_blood
            else:
                # Already captured by this student
                conn.rollback()
                return None, False
                
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to insert flag: {e}")
            return None, False
        finally:
            cursor.close()
            self.release_connection(conn)
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get current leaderboard"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cursor.execute('''
                SELECT * FROM leaderboard LIMIT %s
            ''', (limit,))
            
            return cursor.fetchall()
            
        except Exception as e:
            logger.error(f"Failed to get leaderboard: {e}")
            return []
        finally:
            cursor.close()
            self.release_connection(conn)
    
    def get_student_stats(self, student_id: str) -> Optional[Dict]:
        """Get statistics for a student"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cursor.execute('''
                SELECT * FROM leaderboard WHERE student_id = %s
            ''', (student_id,))
            
            return cursor.fetchone()
            
        except Exception as e:
            logger.error(f"Failed to get student stats: {e}")
            return None
        finally:
            cursor.close()
            self.release_connection(conn)
    
    def close(self):
        """Close all connections"""
        if self.pool:
            self.pool.closeall()
            logger.info("Database connections closed")

