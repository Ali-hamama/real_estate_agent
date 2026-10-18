# Real Estate Agent

An early-stage project to build two agents for working with Dubai real estate information:

1. **Transaction data agent:** prepares data from a transaction database containing historical Dubai real estate transactions.
2. **DLD document retrieval agent:** retrieves information from documents about Dubai Land Department (DLD) services, including property registration procedures and frequently asked questions.

## Current progress

The project is currently building the data foundation for both agents.

- [x] Project structure and Python package setup.
- [x] Historical transaction data processing scripts implemented.
- [x] Data inspection and PDF reporting tools implemented to support data preparation.
- [x] PostgreSQL transaction model, table creation, and CSV import scripts implemented.
- [x] Initial DLD service documents and FAQ collected locally.
- [x] Docker development configuration added.
- [ ] Transaction data agent implementation.
- [ ] DLD document retrieval agent implementation.
- [ ] Automated tests and evaluations.

## Technology

Python 3.12+, pandas, SQLAlchemy, PostgreSQL, and ReportLab. Docker Compose provides a development environment with PostgreSQL and pgAdmin.

## Repository layout

- `app/`: database models and space for the two agents.
- `data/scripts/`: data processing and inspection tools.
- `scripts/`: database setup and import commands.
- `docs/`, `tests/`, `evaluations/`: placeholders for future work.

Raw data, scraped documents, scraper code, generated reports, and local database storage are excluded from Git. Data folders contain `.gitkeep` placeholders; supply your own datasets to run the data workflow.
