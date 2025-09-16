# Data Liberation Project: DOD Child and Domestic Abuse Incidents

Yep, this is a terrible topic.  But the work in this repo is going to help journalists dig into this topic and drive (proper) transparency around this

Docs page: https://www.data-liberation-project.org/requests/dod-child-and-domestic-abuse-incidents/

## How to run locally

1. Install uv: https://docs.astral.sh/uv/getting-started/installation/
1. Note, to run dbt commands within the environment manged by uv, need to run it as: `uv run dbt ...`
1. Open in DuckDB (for querying data locally)

    ```bash
    cd $(git rev-parse --show-toplevel)/dod-abuse/dod_abuse
    uv run python
    >>> import duckdb
    >>> duckdb.sql("attach 'dev.duckdb'")
    >>> duckdb.sql("CALL start_ui()")
    ```
