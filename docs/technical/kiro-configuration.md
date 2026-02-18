# Kiro Configuration for AuronAI

This document describes the complete Kiro setup for the AuronAI trading system project.

## Overview

Kiro has been configured with steering files, hooks, and documentation structure to maintain code quality, enforce risk management rules, and prevent documentation waste.

## Steering Files (Context Rules)

Steering files provide context and rules to Kiro based on the files being edited.

### Always Active

1. **project-standards.md**
   - Python coding standards (PEP 8, type hints, docstrings)
   - Modular architecture principles
   - Error handling requirements
   - Risk management critical rules
   - Naming conventions
   - Language conventions (code in English, docs in Spanish)

2. **no-documentation-waste.md**
   - Prevents creation of temporary documentation files
   - Enforces clean project structure
   - Defines allowed markdown files in root
   - Specifies where different types of documentation should go

3. **documentation-structure.md**
   - Defines docs/ directory structure
   - Separates user docs (Spanish) from technical docs (English)
   - Spec workflow (active in .kiro/specs/, completed in docs/specs/)
   - ADR format and location

### Context-Specific (File Match)

4. **risk-management-rules.md** (matches: *risk*, *trading*, *backtest*)
   - Critical risk management rules (2% max risk, 20% max position)
   - Position sizing formulas (Kelly Criterion)
   - Stop loss requirements
   - Portfolio limits
   - Validation requirements

5. **api-integration-guide.md** (matches: *api*, *claude*, *alpaca*, *yfinance*)
   - Claude API integration best practices
   - Yahoo Finance data retrieval
   - Alpaca trading execution
   - Error handling and fallbacks
   - Rate limits and costs

6. **technical-indicators-reference.md** (matches: *indicator*, *technical*, *analysis*)
   - Reference for all 15+ technical indicators
   - Interpretation guidelines
   - Effective combinations
   - Validation test cases
   - Performance optimization tips

7. **spec-workflow.md** (matches: *spec*/*)
   - Requirements phase guidelines
   - Design phase best practices
   - Task breakdown approach
   - Implementation workflow
   - Spec validation checklist

## Hooks (Automated Actions)

Hooks automatically trigger actions based on IDE events.

### File Edit Hooks

1. **check-api-keys.json** (*.py)
   - Scans for hardcoded API keys
   - Alerts if found
   - Suggests using os.getenv() instead

2. **lint-python-on-save.json** (*.py)
   - Checks PEP 8 compliance
   - Validates type hints presence
   - Checks for docstrings
   - Suggests f-strings over % or .format()

3. **validate-risk-on-save.json** (*risk*.py, *trading*.py, *backtest*.py)
   - Validates max_risk_per_trade <= 2%
   - Validates max_position_size <= 20%
   - Checks for negative/infinite value validations
   - Ensures stop loss calculated before trades

### File Creation Hooks

4. **prevent-doc-waste.json** (*.md)
   - Detects markdown files in wrong locations
   - Alerts if in root (except allowed files)
   - Alerts if in src/
   - Suggests correct location in docs/
   - Deletes temporary files (SUMMARY.md, NOTES.md, etc.)

### User-Triggered Hooks

5. **run-tests-before-commit.json** (manual trigger)
   - Runs quick test suite
   - Verifies dependencies
   - Validates technical indicators
   - Checks demo mode functionality

## Directory Structure

```
AuronAI/
├── src/                          # Source code only
│   ├── trading_agent.py
│   ├── risk_manager.py
│   └── ...
│
├── docs/                         # All documentation
│   ├── user/                     # User-facing docs (Spanish)
│   │   ├── INICIO_RAPIDO.md
│   │   ├── GUIA_PRO.md
│   │   └── ...
│   ├── technical/                # Technical docs (English)
│   │   ├── architecture.md
│   │   ├── this file
│   │   └── ...
│   ├── specs/                    # Completed specs
│   │   └── feature-name/
│   └── decisions/                # ADRs
│       └── NNN-title.md
│
├── .kiro/                        # Kiro configuration
│   ├── specs/                    # Active specs (WIP)
│   │   └── auronai-trading-system/
│   ├── steering/                 # Context rules
│   │   ├── project-standards.md
│   │   ├── risk-management-rules.md
│   │   └── ...
│   └── hooks/                    # Automated actions
│       ├── check-api-keys.json
│       └── ...
│
├── examples/                     # Usage examples
├── tests/                        # Test suite
├── README.md                     # Project overview
├── .env.example                  # Configuration template
└── .gitignore                    # Git ignore rules
```

## Configuration Files

### .env.example

Complete environment configuration template including:
- API keys (Claude, Alpaca)
- Trading configuration
- Risk management parameters
- Technical indicator settings
- Logging configuration
- Backtesting parameters

### .gitignore

Configured to ignore:
- Python artifacts
- Virtual environments
- Environment variables (.env)
- Logs
- Trading results
- Generated charts
- Secrets

## Usage Guidelines

### Working with Specs

1. Create spec in `.kiro/specs/feature-name/`
2. Maintain requirements.md, design.md, tasks.md
3. When complete, move to `docs/specs/feature-name/`
4. Add retrospective.md with learnings

### Documenting Decisions

Create ADR in `docs/decisions/NNN-title.md` following the standard format.

### User Documentation

Add/update files in `docs/user/` in Spanish with emojis for better UX.

### Technical Documentation

Add/update files in `docs/technical/` in English.

### Code Documentation

- Use Google-style docstrings for all public classes and methods
- Include type hints for all function parameters and returns
- Keep inline comments minimal and focused on complex logic
- Extensive documentation goes in docs/, not in code

## Best Practices

### Risk Management

- Always validate risk parameters before trading
- Never exceed 2% risk per trade by default
- Always calculate stop loss before executing trades
- Use ATR-based dynamic stops in advanced mode

### API Integration

- Implement fallbacks for all external APIs
- Use retry logic with exponential backoff
- Cache data when appropriate
- Log all API errors with context

### Code Quality

- Follow PEP 8 strictly
- Use type hints everywhere
- Write comprehensive docstrings
- Keep functions small and focused
- Separate concerns into modules

### Documentation

- Never create temporary docs in root or src/
- Use docs/ structure for all documentation
- Keep README.md brief (< 200 lines)
- Update docs when features change
- Document architectural decisions as ADRs

## Maintenance

This configuration should be:
- Updated when project requirements change
- Reviewed periodically for obsolete rules
- Extended with new hooks as needed
- Documented when significant changes are made

## Next Steps

1. Complete auronai-trading-system spec
2. Implement features according to tasks.md
3. Document important architectural decisions as ADRs
4. Keep docs/user/ updated with new features
5. Add more hooks based on project needs
