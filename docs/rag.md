# Retrieval-Augmented Generation

## Pipeline

```text
Uploaded File
  → Extract Text
  → Persist Content
  → Create Chunks
  → Generate Embeddings
  → Store in Qdrant

User Question
  → Embed Query
  → Vector Search
  → Filter and Rank
  → Build Context
  → Generate Grounded Answer
```

## Components

- document service;
- document extractor;
- chunking service;
- embedding service;
- vector store service;
- retriever service;
- context builder;
- RAG service.

## Data Integrity

Each vector point should connect to:

- user or tenant;
- source document;
- relational chunk;
- optional page or section metadata.

Retrieval filters must prevent cross-user access.

## Quality Controls

- chunk overlap;
- similarity threshold;
- maximum retrieved chunks;
- metadata filtering;
- source deduplication;
- context-length limits;
- empty-retrieval fallback;
- source references.

## Deletion

Deleting a document should remove or invalidate:

- stored file;
- metadata;
- extracted content;
- chunks;
- Qdrant points.
