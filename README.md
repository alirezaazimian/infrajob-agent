# InfraJob Agent

A self-hosted job discovery and opportunity intelligence platform focused on infrastructure, Linux, systems administration, IT operations, and data center roles.

InfraJob Agent collects job postings from multiple sources, normalizes them into a unified format, removes duplicates, filters irrelevant positions, scores relevant opportunities, and stores qualified jobs in PostgreSQL.

The long-term goal is to evolve the platform into a country-aware job intelligence and application assistant capable of identifying high-value international opportunities, evaluating immigration and sponsorship constraints, assisting with application material preparation, and tracking the complete application lifecycle.

---

## Project Status

InfraJob Agent is currently under active development.

The core job discovery pipeline, PostgreSQL persistence layer, job scoring system, structured logging, and application state tracking are operational.

Current development is moving toward:

- Target-market configuration
- Country-aware job discovery
- Additional job sources
- Immigration and sponsorship analysis
- Opportunity scoring
- Automated recurring discovery

AI-assisted job analysis and application automation are planned for later phases.

---

## Current Features

### Job Discovery

- Multi-source job collection
- Remotive API integration
- Greenhouse Job Board integration
- Configurable search terms
- Support for multiple Greenhouse company boards
- Unified job normalization
- Source-aware external job identifiers

### Job Processing

- Cross-source job aggregation
- Job deduplication
- Keyword-based relevance filtering
- Title-aware job scoring
- Positive skill weighting
- Negative keyword penalties
- Minimum qualification threshold
- Score-based ranking

### Reliability

- HTTP error handling
- Connection failure handling
- Request timeout handling
- Fault-tolerant collectors
- Failure isolation between job sources
- Structured application logging
- Console logging
- Persistent file logging

### Database

- PostgreSQL integration
- Persistent job storage
- UPSERT-based duplicate prevention
- Unique external job identifiers
- First-seen tracking
- Last-seen tracking
- Job score persistence

### Application Tracking

- Persistent application states
- Validated status transitions at the application layer
- Application status preservation when jobs are rediscovered

Supported states:

- `new`
- `reviewing`
- `approved`
- `applied`
- `interview`
- `rejected`
- `archived`

---

## Current Architecture

```text
                       ┌─────────────────────┐
                       │     Job Sources     │
                       │                     │
                       │  Remotive           │
                       │  Greenhouse         │
                       └──────────┬──────────┘
                                  │
                                  ▼
                       ┌─────────────────────┐
                       │     Collectors      │
                       └──────────┬──────────┘
                                  │
                                  ▼
                       ┌─────────────────────┐
                       │    Normalization    │
                       └──────────┬──────────┘
                                  │
                                  ▼
                       ┌─────────────────────┐
                       │    Deduplication    │
                       └──────────┬──────────┘
                                  │
                                  ▼
                       ┌─────────────────────┐
                       │      Filtering      │
                       └──────────┬──────────┘
                                  │
                                  ▼
                       ┌─────────────────────┐
                       │       Scoring       │
                       └──────────┬──────────┘
                                  │
                                  ▼
                       ┌─────────────────────┐
                       │ Minimum Score Check │
                       └──────────┬──────────┘
                                  │
                                  ▼
                       ┌─────────────────────┐
                       │   Qualified Jobs    │
                       └──────────┬──────────┘
                                  │
                                  ▼
                       ┌─────────────────────┐
                       │     PostgreSQL      │
                       │                     │
                       │ Job Data            │
                       │ Score               │
                       │ First Seen          │
                       │ Last Seen           │
                       │ Application Status  │
                       └─────────────────────┘
```

---

## Job Normalization

Different job sources expose different schemas.

InfraJob Agent converts source-specific responses into a common internal format before filtering and scoring.

Example normalized job:

```python
{
    "external_id": "greenhouse:4280643009",
    "title": "System Administrator",
    "company": "Example Company",
    "location": "Berlin, Germany",
    "description": "...",
    "url": "https://example.com/job/123",
    "source": "greenhouse"
}
```

Source-aware external IDs are used to prevent collisions between different job providers.

---

## Job Scoring

The current scoring engine uses weighted keyword matching.

Job titles receive stronger weighting than descriptions because title signals are generally more reliable indicators of the actual role.

Examples of positively weighted signals include:

- Linux
- System Administrator
- Infrastructure Engineer
- Systems Engineer
- IT Operations Engineer
- VMware
- vCenter
- ESXi
- Zabbix
- Docker
- Networking
- Veeam
- Bash
- Monitoring
- AWS
- Active Directory

The engine also applies negative penalties to unrelated roles such as:

- Graphic Design
- Marketing
- Sales
- Frontend Development
- Data Science
- Machine Learning
- Software Development roles with weak infrastructure relevance

Qualified jobs must pass a minimum score threshold before being persisted and presented.

The current scoring engine represents technical relevance only.

Future versions will introduce a broader **Opportunity Score** that considers immigration eligibility, sponsorship evidence, language requirements, location restrictions, salary requirements, and employer characteristics.

---

## Target Role Families

InfraJob Agent is primarily designed for infrastructure, systems, and operations roles.

Target role families include:

- Linux Administrator
- System Administrator
- Systems Administrator
- Infrastructure Engineer
- IT Infrastructure Engineer
- Systems Engineer
- IT Operations Engineer
- Infrastructure Operations Engineer
- Data Center Engineer
- Data Center Operations Engineer
- Cloud Operations Engineer
- Platform Operations Engineer
- Technical Infrastructure Engineer
- Virtualization Engineer

DevOps positions may also be considered when the role is primarily focused on infrastructure and operations rather than application development.

---

## International Job Intelligence

A major upcoming capability of InfraJob Agent is country-aware opportunity analysis.

The system is being designed to distinguish between:

```text
Technical Match
        │
        ├── Skills
        ├── Experience
        └── Role relevance

Immigration Match
        │
        ├── Work permit eligibility
        ├── Occupation eligibility
        ├── Salary thresholds
        └── Country-specific rules

Employer Match
        │
        ├── Sponsorship evidence
        ├── International hiring
        ├── Relocation support
        └── Work authorization restrictions

Language Match
        │
        ├── English
        ├── Local-language requirements
        └── Mandatory vs preferred language

                ↓

        Opportunity Score
```

This layer is not yet implemented.

---

## Initial Target Markets

The future country-aware discovery engine is planned around several market groups.

### Core Markets

- Germany
- Denmark
- Ireland
- Austria

### Targeted Markets

- Finland
- Netherlands
- Australia

### Fast-Exit / Bridge Market

- United Arab Emirates

Additional markets may be evaluated selectively according to:

- Immigration eligibility
- Employer sponsorship
- Salary requirements
- Local language requirements
- International hiring policies
- Work authorization restrictions
- Role demand
- Job-market conditions

Country rules and priorities will be configuration-driven rather than permanently hard-coded into the application.

Because immigration and employment rules change over time, future rule definitions will also include metadata such as verification date and authoritative source.

---

## Job Persistence

Qualified jobs are stored in PostgreSQL.

The `external_id` field is unique and is used for UPSERT operations.

When a job is discovered for the first time:

```text
New external_id
      ↓
    INSERT
```

When the same job is discovered again:

```text
Existing external_id
        ↓
      UPDATE
        ↓
Refresh job information
Update score
Update last_seen
Preserve application status
```

This prevents duplicate records while maintaining job history.

---

## First Seen and Last Seen

InfraJob Agent tracks two timestamps for every job:

### `first_seen`

The first time the platform discovered the job.

### `last_seen`

The most recent time the job was discovered again.

Example:

```text
first_seen: 2026-08-28 02:23:01
last_seen:  2026-08-28 02:28:11
```

This provides the foundation for future functionality such as:

- Detecting newly posted jobs
- Identifying stale jobs
- Detecting potentially closed listings
- Tracking job lifetime
- Prioritizing fresh opportunities

---

## Application States

Each persisted job has an application status.

Default status:

```text
new
```

Supported states:

```text
new
reviewing
approved
applied
interview
rejected
archived
```

Example lifecycle:

```text
new
 ↓
reviewing
 ↓
approved
 ↓
applied
 ↓
interview
```

Alternative outcomes may include:

```text
rejected
archived
```

Application state is deliberately preserved when an existing job is rediscovered.

---

## Project Structure

```text
infrajob-agent/
│
├── app/
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── remotive.py
│   │   └── greenhouse.py
│   │
│   ├── __init__.py
│   ├── config_loader.py
│   ├── database.py
│   ├── job_filter.py
│   ├── job_scorer.py
│   ├── job_utils.py
│   ├── logger.py
│   └── normalizers.py
│
├── config/
│   └── sources.json
│
├── logs/
│   └── infrajob-agent.log
│
├── tests/
│
├── .env
├── .env.example
├── .gitignore
├── main.py
├── requirements.txt
└── README.md
```

---

## Requirements

Current core requirements:

- Python 3
- PostgreSQL
- `requests`
- `python-dotenv`
- `psycopg2-binary`

Install project dependencies with:

```bash
pip install -r requirements.txt
```

---

## Python Virtual Environment

Creating an isolated Python environment is recommended.

```bash
python -m venv .venv
```

Activate it on Linux:

```bash
source .venv/bin/activate
```

Verify the active interpreter:

```bash
which python
```

It should point to:

```text
/path/to/infrajob-agent/.venv/bin/python
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## PostgreSQL Setup

Install PostgreSQL on Debian-based systems:

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

Enable and start PostgreSQL:

```bash
sudo systemctl enable --now postgresql
```

Verify the service:

```bash
sudo systemctl is-active postgresql
```

Enter PostgreSQL:

```bash
sudo -u postgres psql
```

Create the project database:

```sql
CREATE DATABASE infrajob;
```

Create a dedicated user:

```sql
CREATE USER infrajob_user WITH PASSWORD 'your-secure-password';
```

Grant database privileges:

```sql
GRANT ALL PRIVILEGES ON DATABASE infrajob TO infrajob_user;
```

Connect to the database:

```sql
\c infrajob
```

Grant schema privileges:

```sql
GRANT ALL ON SCHEMA public TO infrajob_user;
```

Exit:

```sql
\q
```

Test the connection:

```bash
psql -h localhost -U infrajob_user -d infrajob
```

---

## Environment Configuration

Create a `.env` file in the project root:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=infrajob
DB_USER=infrajob_user
DB_PASSWORD=your-secure-password
```

An example configuration should be stored in `.env.example`:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=infrajob
DB_USER=infrajob_user
DB_PASSWORD=
```

Never commit the real `.env` file.

---

## Database Schema

The current `jobs` table contains:

```text
id
external_id
title
company
location
description
url
source
score
status
first_seen
last_seen
```

Conceptually:

```sql
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(255) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    company TEXT,
    location TEXT,
    description TEXT,
    url TEXT,
    source VARCHAR(50),
    score INTEGER,
    status VARCHAR(30) NOT NULL DEFAULT 'new',
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Running the Agent

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Run:

```bash
python main.py
```

The pipeline will:

```text
Load source configuration
        ↓
Collect jobs
        ↓
Normalize jobs
        ↓
Remove duplicates
        ↓
Filter irrelevant jobs
        ↓
Calculate relevance score
        ↓
Apply minimum score threshold
        ↓
Rank qualified jobs
        ↓
Persist jobs in PostgreSQL
        ↓
Print results
        ↓
Write structured logs
```

---

## Logging

Application logs are written to:

```text
logs/infrajob-agent.log
```

View recent logs:

```bash
tail -n 20 logs/infrajob-agent.log
```

Follow logs in real time:

```bash
tail -f logs/infrajob-agent.log
```

Logging currently captures:

- Application startup
- Source collection activity
- Number of returned jobs
- HTTP failures
- Timeouts
- Connection failures
- Database persistence events
- Pipeline completion statistics

---

## Current Job Sources

### Remotive

Remotive provides remote job listings through its public API.

The current configuration searches several infrastructure-related terms.

Example:

```json
{
  "search_terms": [
    "linux",
    "system administrator",
    "infrastructure",
    "systems engineer",
    "devops"
  ]
}
```

Because API searches may return overlapping results, source-aware deduplication is applied.

### Greenhouse

InfraJob Agent supports public Greenhouse Job Board APIs.

Multiple organizations can be configured using their Greenhouse board tokens.

Example:

```json
{
  "boards": [
    {
      "board_name": "example-company",
      "company": "Example Company"
    }
  ]
}
```

---

## Source Configuration

Current source configuration is stored in:

```text
config/sources.json
```

Example:

```json
{
  "remotive": {
    "search_terms": [
      "linux",
      "system administrator",
      "infrastructure",
      "systems engineer",
      "devops"
    ]
  },
  "greenhouse": {
    "boards": [
      {
        "board_name": "example-company",
        "company": "Example Company"
      }
    ]
  }
}
```

Future versions will move additional search behavior and target-market strategy into configuration files.

---

## Roadmap

### Phase 1 — Job Discovery Pipeline

- [x] Multi-source job collection
- [x] Remotive integration
- [x] Greenhouse integration
- [x] Unified normalization
- [x] Source-aware job identifiers
- [x] Deduplication
- [x] Relevance filtering
- [x] Weighted scoring
- [x] Minimum score threshold
- [x] Fault-tolerant collectors
- [x] Structured logging

---

### Phase 2 — Persistence and State

- [x] PostgreSQL integration
- [x] Persistent job storage
- [x] UPSERT support
- [x] Duplicate prevention
- [x] First-seen tracking
- [x] Last-seen tracking
- [x] Application state tracking
- [x] Application status validation

---

### Phase 3 — Job Intelligence

- [ ] Target-market configuration
- [ ] Country-aware discovery
- [ ] Target-role configuration
- [ ] Additional job sources
- [ ] Employer career-page discovery
- [ ] Immigration eligibility rules
- [ ] Occupation eligibility analysis
- [ ] Sponsorship signal detection
- [ ] Work-authorization restriction detection
- [ ] Language requirement detection
- [ ] Salary-threshold validation
- [ ] Employer international-hiring signals
- [ ] Relocation-support detection
- [ ] Opportunity scoring

---

### Phase 4 — Real Search Operations

- [ ] High-priority opportunity identification
- [ ] New-job detection
- [ ] Country-specific result summaries
- [ ] Application review queue
- [ ] Automated recurring discovery
- [ ] Daily opportunity reports

At this stage, the system should already be used for real-world job discovery while development continues.

---

### Phase 5 — AI Assistance

- [ ] Semantic job-to-profile matching
- [ ] Job-description analysis
- [ ] Missing-skill detection
- [ ] Application-risk analysis
- [ ] CV relevance analysis
- [ ] CV tailoring
- [ ] Cover-letter generation
- [ ] Application recommendation explanations

AI components will support decision-making rather than replace deterministic eligibility and filtering rules.

---

### Phase 6 — Application Workflow

- [ ] Approval workflow
- [ ] Application preparation
- [ ] Employer/contact discovery
- [ ] Outreach workflow
- [ ] Email integration
- [ ] Application submission tracking
- [ ] Interview tracking
- [ ] Follow-up tracking

The platform should not automatically submit applications without explicit workflow controls and approval mechanisms.

---

### Phase 7 — Infrastructure and Operations

- [ ] Docker
- [ ] Background workers
- [ ] Scheduler
- [ ] FastAPI service
- [ ] Health checks
- [ ] Metrics
- [ ] Monitoring
- [ ] Observability
- [ ] CI/CD
- [ ] Automated tests
- [ ] Deployment automation

---

## Planned Opportunity Scoring

The current score represents technical job relevance.

A future opportunity engine will evaluate several dimensions independently.

Example:

```text
Technical Skill Match       88
Role Match                  95
Experience Match            90
Country Fit                 85
Immigration Fit             90
Employer Sponsorship        80
Language Fit               100
Salary Eligibility          90
--------------------------------
Opportunity Score           89
```

Some conditions may act as hard blockers instead of simple penalties.

Examples:

```text
Local work authorization required
No visa sponsorship
Mandatory unsupported language
Salary below immigration threshold
Occupation not eligible for required permit
Country-specific legal restriction
```

This prevents technically relevant but practically inaccessible jobs from dominating the results.

---

## Planned Immigration Rule Model

Immigration rules change over time.

Future country rules should therefore contain metadata instead of being treated as permanent constants.

Example concept:

```json
{
  "country": "Example Country",
  "rule": "qualified_worker_route",
  "enabled": true,
  "source_type": "official",
  "last_verified": "YYYY-MM-DD",
  "valid_from": "YYYY-MM-DD",
  "valid_until": null
}
```

The goal is to keep immigration intelligence:

- Traceable
- Updateable
- Source-aware
- Time-aware
- Separate from core technical scoring

---

## Design Principles

InfraJob Agent follows several design principles.

### Configuration Over Hard-Coding

Search sources, market priorities, role families, and future country rules should be configurable.

### Deterministic Rules Before AI

Hard eligibility conditions should be handled by explicit rules before an AI model is asked for subjective analysis.

### Persistent State

Jobs and application states must survive process restarts.

### Source Isolation

Failure of one external source should not stop the entire pipeline.

### Explainable Scoring

The system should be able to explain why a job received a particular score.

### Human-Controlled Applications

Future automation should assist with preparation and prioritization while preserving explicit control over external applications and outreach.

---

## Current Limitations

The current version does not yet:

- Perform immigration eligibility analysis
- Verify visa sponsorship
- Detect international hiring history
- Analyze employer relocation policies
- Evaluate salary against immigration thresholds
- Perform semantic or LLM-based job matching
- Tailor CVs automatically
- Generate application materials
- Send applications
- Send outreach emails
- Run automatically on a schedule
- Provide a web API or dashboard
- Include production monitoring

These capabilities are part of the roadmap and should not be considered implemented.

---

## Security

Sensitive configuration such as database credentials must remain outside version control.

The following should never be committed:

```text
.env
database passwords
API secrets
authentication tokens
private keys
```

Use `.env.example` to document required environment variables without exposing real credentials.

---

## Development Philosophy

InfraJob Agent is being developed incrementally.

Each milestone should produce a working system rather than depending on a large unfinished architecture.

The intended evolution is:

```text
Job Collector
      ↓
Job Discovery Pipeline
      ↓
Persistent Job Database
      ↓
Job Intelligence Platform
      ↓
Country-Aware Opportunity Engine
      ↓
AI-Assisted Application System
```

The project prioritizes practical job discovery before adding advanced automation.

---

## License

A license has not yet been selected.

---

## Disclaimer

InfraJob Agent is a software project designed to assist with job discovery and opportunity analysis.

Immigration laws, salary requirements, employment regulations, visa policies, and occupation lists can change.

Future immigration-related functionality should rely on authoritative and regularly verified sources and should be treated as decision-support information rather than legal advice.