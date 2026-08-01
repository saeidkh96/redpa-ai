# RedPA Research 3.2.2

## Added
- dedicated evidence cleaner;
- strict prompt builder;
- grounded-summary validator;
- prompt-injection filtering;
- lexical grounding validation.

## Changed
- ResearchService delegates prompt construction and validation;
- dirty search snippets are cleaned before ranking and summarization;
- invalid LLM summaries use deterministic fallback output.
