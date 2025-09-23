# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **Escalation Monitor** application built for Vercel deployment with Python 3.12. The application consists of two main components:

1. **Daily Cron Job** (`/api/cron`) - Processes RSS feeds daily and calculates escalation scores (1-10 scale)
2. **Dashboard UI** (`/`) - Web interface displaying current escalation score and metrics

## Architecture

### Vercel Functions Structure
- `api/app.py` - FastAPI application serving dashboard API endpoints (`/score`, `/metrics`)
- `api/cron.py` - HTTP handler for daily cron job (protected by `CRON_SECRET` environment variable)
- `public/index.html` - Static dashboard UI served from Vercel's CDN

### RSS Feed Processing System
- `src/feeds/base.py` - Abstract `FeedSource` class for RSS/Atom feed processing
- `src/feeds/` - Child classes implement `map_entry()` method for source-specific parsing
- Feed output format: `{source_name, date, result: "ok"|"error", error_message?, items: [{date, text, url}]}`

### Data Flow
1. **Cron trigger** (daily 4:00 UTC) → `api/cron.py` → `src/pipeline.py`
2. **Pipeline** processes multiple RSS feeds in parallel using `asyncio` + `httpx`
3. **Results** stored via `src/storage.py` (currently dummy implementation)
4. **Dashboard** fetches data via FastAPI endpoints in `api/app.py`

## Development Commands

### Local Development
```bash
# Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run FastAPI locally (for testing API endpoints)
uvicorn api.app:app --reload
```

### Vercel Deployment
```bash
# Deploy to Vercel
vercel --prod

# Set environment variable for cron security
vercel env add CRON_SECRET
```

## Key Configuration

### Vercel Settings (`vercel.json`)
- **Runtime**: Python 3.12
- **Region**: fra1 (Frankfurt)
- **Cron Schedule**: Daily at 4:00 UTC
- **Function Timeout**: 300 seconds

### RSS Feed Integration
- Uses `feedparser` library for robust RSS/Atom parsing
- `httpx` for async HTTP requests with 20-second timeouts
- Child classes of `FeedSource` handle source-specific parsing logic

## Environment Variables
- `CRON_SECRET` - Required for cron job authentication (set in Vercel dashboard)

## Agno Framework Reference
- **Agno Documentation**: Available at `~/Downloads/Agno-Framework-Anweisung.md`
- This project may integrate with Agno agents for advanced AI functionality
- Agno provides Agent, Memory, Storage, and SQLite/PostgreSQL integration capabilities
- Reference the Agno documentation when implementing AI agent features or persistent memory systems

## Important Development Rules
- **NEVER automatically truncate or shorten text content** - Always show full text for analysis
- Only truncate text when explicitly instructed by the user
- Feed processing and markdown output must preserve complete article content
- **For code quality checks**: Always use `mcp__ide__getDiagnostics` instead of `pylint` command for linting and type checking