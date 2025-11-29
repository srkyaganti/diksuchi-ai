-- Migration: Drop embeddings table (switching to ChromaDB)
-- This migration removes the embeddings table and pgvector dependency
-- Embeddings are now stored in ChromaDB via the Python RAG service

-- Drop the embeddings table (CASCADE will drop foreign keys)
DROP TABLE IF EXISTS "embeddings" CASCADE;

-- Optionally drop the pgvector extension if no longer needed
-- Uncomment the following line if you want to completely remove pgvector
-- DROP EXTENSION IF EXISTS vector;
