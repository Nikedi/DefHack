#!/usr/bin/env python3
"""
DefHack Database Inspector
Direct database queries to view observations and documents
"""
import asyncio
import asyncpg
import json
from datetime import datetime
from typing import List, Dict, Any

class DefHackDatabaseInspector:
    """Direct database inspection for DefHack system"""
    
    def __init__(self, db_url: str = "postgresql://postgres:postgres@localhost:5432/defhack"):
        self.db_url = db_url
        
    async def connect(self):
        """Connect to the database"""
        self.conn = await asyncpg.connect(self.db_url)
        
    async def disconnect(self):
        """Disconnect from database"""
        if hasattr(self, 'conn'):
            await self.conn.close()
    
    async def get_all_observations(self) -> List[Dict[str, Any]]:
        """Get all tactical sensor observations"""
        query = """
        SELECT time, mgrs, what, amount, confidence, sensor_id, unit, observer_signature, received_at
        FROM sensor_reading 
        ORDER BY time DESC
        """
        
        rows = await self.conn.fetch(query)
        observations = []
        
        for row in rows:
            obs = dict(row)
            # Convert datetime objects to strings for JSON serialization
            obs['time'] = obs['time'].isoformat() if obs['time'] else None
            obs['received_at'] = obs['received_at'].isoformat() if obs['received_at'] else None
            observations.append(obs)
            
        return observations
    
    async def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all intelligence documents"""
        query = """
        SELECT id, title, version, object_key, checksum, source_type, lang, 
               published_at, origin, adversary, created_at
        FROM intel_doc 
        ORDER BY created_at DESC
        """
        
        rows = await self.conn.fetch(query)
        documents = []
        
        for row in rows:
            doc = dict(row)
            # Convert date/datetime objects to strings
            doc['published_at'] = doc['published_at'].isoformat() if doc['published_at'] else None
            doc['created_at'] = doc['created_at'].isoformat() if doc['created_at'] else None
            documents.append(doc)
            
        return documents
    
    async def get_document_chunks(self, doc_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get chunks for a specific document"""
        query = """
        SELECT id, doc_id, chunk_idx, text, page, para, line_start, line_end, 
               step_id, section, embedding
        FROM doc_chunk 
        WHERE doc_id = $1
        ORDER BY chunk_idx
        LIMIT $2
        """
        
        rows = await self.conn.fetch(query, doc_id, limit)
        chunks = []
        
        for row in rows:
            chunk = dict(row)
            # Truncate long text and embedding for display
            if chunk['text'] and len(chunk['text']) > 200:
                chunk['text_preview'] = chunk['text'][:200] + "..."
                chunk['text_length'] = len(chunk['text'])
            else:
                chunk['text_preview'] = chunk['text']
                chunk['text_length'] = len(chunk['text']) if chunk['text'] else 0
                
            # Don't include full embedding in display (too long)
            if chunk['embedding']:
                chunk['has_embedding'] = True
                chunk['embedding_preview'] = chunk['embedding'][:50] + "..." if len(chunk['embedding']) > 50 else chunk['embedding']
            else:
                chunk['has_embedding'] = False
                
            del chunk['embedding']  # Remove full embedding from output
            chunks.append(chunk)
            
        return chunks
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {}
        
        # Count observations
        obs_count = await self.conn.fetchval("SELECT COUNT(*) FROM sensor_reading")
        stats['total_observations'] = obs_count
        
        # Count documents
        doc_count = await self.conn.fetchval("SELECT COUNT(*) FROM intel_doc")
        stats['total_documents'] = doc_count
        
        # Count chunks
        chunk_count = await self.conn.fetchval("SELECT COUNT(*) FROM doc_chunk")
        stats['total_chunks'] = chunk_count
        
        # Recent activity
        recent_obs = await self.conn.fetchval(
            "SELECT COUNT(*) FROM sensor_reading WHERE received_at > NOW() - INTERVAL '24 hours'"
        )
        stats['observations_last_24h'] = recent_obs
        
        recent_docs = await self.conn.fetchval(
            "SELECT COUNT(*) FROM intel_doc WHERE created_at > NOW() - INTERVAL '24 hours'"
        )
        stats['documents_last_24h'] = recent_docs
        
        return stats

async def display_observations(inspector):
    """Display all sensor observations"""
    print("📡 TACTICAL SENSOR OBSERVATIONS")
    print("=" * 80)
    
    observations = await inspector.get_all_observations()
    
    if not observations:
        print("No observations found in database.")
        return
    
    for i, obs in enumerate(observations, 1):
        print(f"\n[{i}] Observation #{i}")
        print(f"    Time: {obs['time']}")
        print(f"    Location (MGRS): {obs['mgrs']}")
        print(f"    Target: {obs['what']}")
        if obs['amount']:
            print(f"    Amount: {obs['amount']}")
        print(f"    Confidence: {obs['confidence']}%")
        print(f"    Sensor ID: {obs['sensor_id']}")
        if obs['unit']:
            print(f"    Unit: {obs['unit']}")
        print(f"    Observer: {obs['observer_signature']}")
        print(f"    Received: {obs['received_at']}")

async def display_documents(inspector):
    """Display all intelligence documents"""
    print("\n📚 INTELLIGENCE DOCUMENTS")
    print("=" * 80)
    
    documents = await inspector.get_all_documents()
    
    if not documents:
        print("No documents found in database.")
        return
        
    for i, doc in enumerate(documents, 1):
        print(f"\n[{i}] Document ID: {doc['id']}")
        print(f"    Title: {doc['title']}")
        if doc['version']:
            print(f"    Version: {doc['version']}")
        print(f"    Type: {doc['source_type']}")
        print(f"    Language: {doc['lang'] or 'Not specified'}")
        if doc['published_at']:
            print(f"    Published: {doc['published_at']}")
        if doc['origin']:
            print(f"    Origin: {doc['origin']}")
        if doc['adversary']:
            print(f"    Adversary: {doc['adversary']}")
        print(f"    Object Key: {doc['object_key']}")
        print(f"    Checksum: {doc['checksum'][:16]}...")
        print(f"    Uploaded: {doc['created_at']}")
        
        # Show some chunks for this document
        chunks = await inspector.get_document_chunks(doc['id'], 3)
        print(f"    Chunks: {len(chunks)} (showing first 3)")
        for j, chunk in enumerate(chunks, 1):
            print(f"      [{j}] Page {chunk['page']}, Para {chunk['para']}: {chunk['text_preview']}")

async def display_database_stats(inspector):
    """Display database statistics"""
    print("\n📊 DATABASE STATISTICS")
    print("=" * 80)
    
    stats = await inspector.get_database_stats()
    
    print(f"Total Observations: {stats['total_observations']}")
    print(f"Total Documents: {stats['total_documents']}")
    print(f"Total Document Chunks: {stats['total_chunks']}")
    print(f"Observations (Last 24h): {stats['observations_last_24h']}")
    print(f"Documents (Last 24h): {stats['documents_last_24h']}")

async def main():
    """Main inspection function"""
    inspector = DefHackDatabaseInspector()
    
    try:
        print("🔍 DefHack Database Inspector")
        print("=" * 80)
        print("Connecting to database...")
        
        await inspector.connect()
        print("✅ Connected successfully!")
        
        # Display statistics first
        await display_database_stats(inspector)
        
        # Display observations
        await display_observations(inspector)
        
        # Display documents
        await display_documents(inspector)
        
        print(f"\n🎉 Database inspection complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        await inspector.disconnect()

if __name__ == "__main__":
    asyncio.run(main())