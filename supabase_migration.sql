-- Run this in the Supabase SQL Editor (one time setup)
-- https://supabase.com/dashboard → your project → SQL Editor

-- 1. Enable pgvector extension
create extension if not exists vector;

-- 2. Create the per-chunk table
--    embedding is 1024-dim: matches voyage-4-large
create table if not exists document_chunks (
  id          bigserial primary key,
  notebook_id text      not null,
  doc_name    text      not null,
  chunk_index int       not null,
  content     text      not null,
  embedding   vector(1024),
  created_at  timestamptz default now()
);

-- 3. Indexes
create index if not exists document_chunks_notebook_idx
  on document_chunks (notebook_id);

create index if not exists document_chunks_embedding_idx
  on document_chunks using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

-- 4. RPC used by query_context for vector search
create or replace function match_chunks(
  query_embedding   vector(1024),
  match_notebook_id text,
  match_count       int default 6
)
returns table (content text, similarity float)
language sql stable
as $$
  select
    content,
    1 - (embedding <=> query_embedding) as similarity
  from document_chunks
  where notebook_id = match_notebook_id
    and embedding is not null
  order by embedding <=> query_embedding
  limit match_count;
$$;
