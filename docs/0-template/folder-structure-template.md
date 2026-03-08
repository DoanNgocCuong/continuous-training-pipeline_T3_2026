# Folder Structure Template

This document defines the standard folder structure for documentation in this project, following the Diátaxis framework.

---

## Overview

```
docs/
├── 0-template/                      ## TEMPLATE
│   ├── folder-structure-template.md             ## This file
│   └── standard-logging-template.md
│
├── 1-tutorials/                      ## TUTORIALS
│   ├── local-development.md              ## "Can you teach me to...?"
│   ├── first-contribution.md             ## "From zero to first PR"
│   └── ...
│
├── 2-how-to/                              ## HOW-TO
│   ├── deployment.md                     ## "How do I deploy?"
│   ├── contributing.md                   ## "How do I contribute?"
│   ├── runbooks/                          ## Incident procedures
│   │   ├── RUNBOOK-001-xxx.md
│   │   └── RUNBOOK-002-xxx.md
│   └── postmortem/                        ## Post-incident reports
│       ├── PM-001-xxx.md
│       └── PM-002-xxx.md
│
├── 3-reference/                           ## REFERENCE
│   ├── SDD.md                           ## System design
│   ├── API.md                           ## API documentation
│   ├── GLOSSARY.md                      ## Terminology
│   └── CHANGELOG.md                     ## Version history
│
├── 4-explanation/                                 ## EXPLANATION
│   ├── ADR-001-xxx.md             ## Architectural decisions
│   ├── ADR-002-xxx.md
│   └── ...
│
└── 5-CKP_detail_implement_docs/     ## IMPLEMENTATION
    ├── implement-docs-001/
    │   ├── implement-001.1-xxx.md
    │   └── implement-001.2-xxx.md
    ├── implement-docs-002/
    └── ...
```

---

## Diátaxis Framework

### 1. Tutorials
**Purpose**: Learning - "Can you teach me to...?"
**Audience**: New users, beginners
**Characteristics**:
- Step-by-step instructions
- Assume no prior knowledge
- Build a complete understanding

### 2. How-To Guides
**Purpose**: Task-oriented - "How do I...?"
**Audience**: Practitioners with some knowledge
**Characteristics**:
- Focus on specific tasks
- Skip background explanation
- Assume familiarity with basics

### 3. Reference
**Purpose**: Information - "What is...?"
**Audience**: All users
**Characteristics**:
- Comprehensive, accurate
- No explanation, just facts
- Technical depth

### 4. Explanation
**Purpose**: Understanding - "Why...?"
**Audience**: Curious users
**Characteristics**:
- Discusses choices and trade-offs
- Provides background
- Links to ADRs

### 5. Implementation Docs
**Purpose**: Technical details - "How does it work?"
**Audience**: Developers
**Characteristics**:
- Code-level details
- Algorithms and architecture
- Integration points

---

## Template Files

### 0-template/
Contains templates for creating new documentation files.

### Naming Convention
- Use kebab-case: `my-new-document.md`
- For runbooks: `RUNBOOK-XXX-description.md`
- For postmortems: `PM-XXX-description.md`
- For ADRs: `ADR-XXX-title.md`
- For implementation: `implement-XXX.N-title.md`

---

*Last updated: 2026-03-08*
