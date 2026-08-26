# InfraJob Agent

A self-hosted job discovery and filtering platform focused on Linux System Administration, Infrastructure, and related engineering roles.

InfraJob Agent collects job postings from multiple sources, converts them into a unified internal format, removes duplicates, filters irrelevant positions, and scores relevant opportunities based on infrastructure-related skills and keywords.

The project is being developed incrementally as a practical Linux, infrastructure, automation, and Python engineering project.

---

## Current Status

🚧 Active Development

The core multi-source job discovery pipeline is operational.

Current pipeline:

```text
Job Sources
    │
    ├── Remotive API
    │
    └── Greenhouse Job Boards
            │
            ▼
       Normalization
            │
            ▼
       Deduplication
            │
            ▼
         Filtering
            │
            ▼
          Scoring
            │
            ▼
     Qualified Jobs
```

---

## Implemented Features

### Multi-Source Job Collection

The platform currently collects job postings from:

- Remotive API
- Greenhouse-powered company career boards

The collector architecture is designed to support additional job sources in future releases.

### Job Normalization

Different job sources return different data structures.

InfraJob Agent converts collected jobs into a common internal schema:

```text
external_id
title
company
location
description
url
source
```

This allows the rest of the application to process jobs independently of their original source.

### Deduplication

Duplicate job postings are removed using source-aware external identifiers.

Example:

```text
greenhouse:4280631009
remotive:123456
```

This prevents jobs collected multiple times from being processed repeatedly.

### Infrastructure Job Filtering

Jobs are filtered using keywords associated with roles such as:

- Linux System Administrator
- Systems Administrator
- Infrastructure Engineer
- Systems Engineer
- DevOps Engineer
- Site Reliability Engineer
- IT Operations Engineer
- Cloud Support Engineer
- Service Desk Engineer

Both job titles and descriptions can be evaluated.

### Job Scoring

Relevant jobs are scored based on infrastructure technologies and skills including:

- Linux
- Ubuntu
- RHEL / Red Hat
- VMware
- ESXi
- vCenter
- Zabbix
- Docker
- Bash
- AWS
- Networking
- Monitoring
- Veeam
- Active Directory

Negative keywords are also used to reduce scores for unrelated software development and data-focused roles.

Scores are normalized to:

```text
0 - 100
```

A minimum score threshold prevents weak matches from appearing in the final results.

### External Source Configuration

Job sources and search terms are stored separately from the application logic:

```text
config/sources.json
```

This makes it possible to add new Greenhouse job boards or modify search terms without changing the main application code.

---

## Example Output

```text
InfraJob Agent
============================================================

Searching Remotive: linux
Searching Remotive: system administrator
Searching Remotive: infrastructure
Searching Remotive: systems engineer
Searching Remotive: devops

Collecting Greenhouse: Quantiq

============================================================
Remotive jobs: 90
Greenhouse jobs: 11
Total jobs: 101
Unique jobs: 29
Relevant jobs: 11
============================================================

1. System Administrator (Linux and Datacenter)
   Company: Quantiq
   Location: Austin, TX
   Source: greenhouse
   Score: 100/100

2. IT Operations Engineer
   Company: Quantiq
   Location: Austin, TX
   Source: greenhouse
   Score: 65/100

3. DevOps Engineer
   Company: Quantiq
   Location: Austin, TX
   Source: greenhouse
   Score: 55/100
```

Results depend on currently available job postings.

---

## Project Structure

```text
infrajob-agent/
├── app/
│   ├── collectors/
│   │   ├── greenhouse.py
│   │   └── remotive.py
│   ├── config_loader.py
│   ├── job_filter.py
│   ├── job_scorer.py
│   ├── job_utils.py
│   └── normalizers.py
│
├── config/
│   └── sources.json
│
├── tests/
├── .env.example
├── .gitignore
├── main.py
├── requirements.txt
└── README.md
```

---

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd infrajob-agent
```

Create a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
python main.py
```

---

## Technology Stack

Currently implemented:

- Python 3
- Requests
- REST APIs
- JSON configuration
- Git / GitHub

Planned infrastructure components will be added as development progresses.

---

## Roadmap

Planned development includes:

- Resilient collectors and exception handling
- Structured application logging
- Additional ATS/job sources
- Improved job relevance scoring
- Geographic and remote-work filtering
- PostgreSQL persistence
- Application state tracking
- Docker containerization
- Scheduled job collection
- AI-assisted job analysis
- CV/job matching
- Cover letter generation
- Email application workflow
- Monitoring and observability
- CI/CD with GitHub Actions

The long-term goal is to build a self-hosted job intelligence and application automation system for infrastructure-focused job searches.

---

## Development Philosophy

InfraJob Agent is being built incrementally.

Each development milestone introduces a practical engineering concept such as:

- API integration
- Data normalization
- Deduplication
- Configuration management
- Filtering and scoring
- Error handling
- Persistence
- Containerization
- Monitoring
- Automation

The goal is not only to automate job discovery, but also to demonstrate practical Linux, infrastructure, and automation engineering skills.

---

## License

This project is currently under active development.