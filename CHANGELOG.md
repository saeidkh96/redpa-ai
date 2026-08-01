# Phase 3.2 Changelog

## Added

- deterministic evidence ranking;
- duplicate removal;
- domain-aware source scoring;
- evidence selection;
- confidence estimation;
- Python response formatter;
- deterministic citation generation;
- research quality metrics;
- fallback summary generation.

## Changed

- the LLM now generates summary text only;
- the LLM no longer generates citations, Sources, Markdown structure,
  confidence, or JSON;
- only ranked evidence is included in the final response.

## Compatibility

Compatible with the existing Phase 3.1 Research Node and result schema.
