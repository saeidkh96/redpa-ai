# Research Pipeline

## Purpose

The research workflow retrieves current web evidence and produces a source-grounded synthesis.

## Stages

1. query preparation;
2. web search;
3. evidence normalization;
4. duplicate removal;
5. ranking;
6. bounded context construction;
7. model synthesis;
8. metadata persistence.

## Reliability

The implementation separates search failures from model failures and records evidence metadata for inspection.

## Current Search Provider

Public web search is performed through DDGS without requiring a paid API key.
