# ADR-0002: Spring Boot Policy Engine

Status: Accepted

## Context

Governance logic benefits from a separately deployable, strongly structured
service boundary.

## Decision

Policy evaluation is implemented as a Java 21 / Spring Boot microservice.

## Consequences

- policy logic is isolated from agent runtime code;
- Spring Boot skills are represented by a real architectural component;
- RedPA now has a cross-language service contract that must remain versioned.
