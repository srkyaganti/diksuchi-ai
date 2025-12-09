import sqlite3
import networkx as nx
import json
import logging
from typing import List, Tuple, Dict, Any

logger = logging.getLogger(__name__)

class LocalGraph:
    """
    A lightweight Knowledge Graph using SQLite for persistence and NetworkX for analysis.
    Designed for local RAG pipelines where Neo4j is overkill.
    """
    
    def __init__(self, db_path: str = "data/defense_graph.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Nodes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    type TEXT,
                    content TEXT,
                    metadata JSON
                )
            """)
            
            # Edges table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS edges (
                    source_id TEXT,
                    target_id TEXT,
                    relation TEXT,
                    weight REAL DEFAULT 1.0,
                    PRIMARY KEY (source_id, target_id, relation),
                    FOREIGN KEY(source_id) REFERENCES nodes(id),
                    FOREIGN KEY(target_id) REFERENCES nodes(id)
                )
            """)
            
            # Indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)")
            
            conn.commit()

    def add_node(self, node_id: str, node_type: str, content: str = "", metadata: Dict = None):
        """Add or update a node."""
        if metadata is None:
            metadata = {}

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO nodes (id, type, content, metadata) VALUES (?, ?, ?, ?)",
                (node_id, node_type, content, json.dumps(metadata))
            )
            conn.commit()
        logger.debug(f"Added node: {node_id} (type: {node_type}) to knowledge graph")

    def add_edge(self, source_id: str, target_id: str, relation: str, weight: float = 1.0):
        """Add a directed edge."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Ensure nodes exist (optional, but good for integrity)
            # For speed, we assume nodes are added first or we use IGNORE
            cursor.execute(
                "INSERT OR IGNORE INTO edges (source_id, target_id, relation, weight) VALUES (?, ?, ?, ?)",
                (source_id, target_id, relation, weight)
            )
            conn.commit()
        logger.debug(f"Added reference edge: {source_id} -> {target_id} (relation: {relation})")

    def get_neighbors(self, node_id: str, relation: str = None) -> List[Dict]:
        """Get neighboring nodes, optionally filtered by relation type."""
        query = """
            SELECT n.id, n.type, n.content, n.metadata, e.relation
            FROM edges e
            JOIN nodes n ON e.target_id = n.id
            WHERE e.source_id = ?
        """
        params = [node_id]
        
        if relation:
            query += " AND e.relation = ?"
            params.append(relation)
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            rows = cursor.execute(query, params).fetchall()
            
        return [
            {
                "id": row[0],
                "type": row[1],
                "content": row[2],
                "metadata": json.loads(row[3]),
                "relation": row[4]
            }
            for row in rows
        ]

    def to_networkx(self) -> nx.DiGraph:
        """Load the entire graph into NetworkX for complex analysis."""
        G = nx.DiGraph()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Add nodes
            nodes = cursor.execute("SELECT id, type, metadata FROM nodes").fetchall()
            for nid, ntype, meta in nodes:
                G.add_node(nid, type=ntype, **json.loads(meta))
                
            # Add edges
            edges = cursor.execute("SELECT source_id, target_id, relation, weight FROM edges").fetchall()
            for src, dst, rel, w in edges:
                G.add_edge(src, dst, relation=rel, weight=w)
                
        return G
