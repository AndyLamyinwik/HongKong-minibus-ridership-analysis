# Analytical SQL queries

These six read-only SQLite queries use the validated Phase 2 tables in `data/processed/transport.sqlite`. They create no tables or views and do not modify the database. Each query is a single `SELECT` statement with Common Table Expressions; annual growth, monthly growth and share calculations also demonstrate window functions. The analytical scope remains January 2015–December 2025, with complete monthly coverage established by the preparation checks.

| File | Output grain and rows | Calculation |
| --- | --- | --- |
| `annual_ridership.sql` | Year × five modes; 55 rows | Sum twelve monthly flows; annual absolute change and year-over-year percentage change |
| `monthly_yoy.sql` | Month × five modes; 660 rows | Compare with the same calendar month one year earlier |
| `annual_market_share.sql` | Year × four comparison modes; 44 rows | Annual mode journeys divided by the annual comparison-group sum |
| `monthly_market_share.sql` | Month × four comparison modes; 528 rows | Monthly mode journeys divided by the monthly comparison-group sum |
| `recovery_2019.sql` | Five modes; 5 rows | Full-year 2025 journeys relative to full-year 2019 journeys |
| `fleet_normalized.sql` | Month × GMB/RMB; 264 rows | Average daily journeys divided by month-end licensed vehicles |

Outputs sort chronologically and then alphabetically by mode; the recovery table sorts alphabetically by mode. Values remain unrounded. Passenger totals and absolute changes use **thousand journeys**; the daily source rate uses **thousand journeys per day**. Growth, recovery and shares are percentages; a difference between two shares is expressed in percentage points. Recovery can exceed 100%. A percentage change is `(current − baseline) / baseline × 100`; recovery is `current / baseline × 100`. Undefined divisions return SQL `NULL`. The first annual year and the first twelve monthly observations per mode have no prior-year growth value within the study window.

The share denominator is **GMB + RMB + MTR + franchised buses**. PLB is excluded from share queries because PLB already equals GMB + RMB. This is a defined comparison group, not Hong Kong's entire public transport market. The prepared MTR and bus totals are used once each; their component boundaries and the July 2023 Citybus/NWFB merger are handled by Phase 2. The annual share is calculated from annual totals, rather than by averaging monthly percentages.

`measurement_basis` and `includes_estimates` accompany aggregate share, recovery and fleet outputs. RMB passenger volumes remain estimates, and PLB totals include that estimated component. Share denominators therefore also contain estimated volumes even for modes whose own numerator is reported. Annual provisional and revised flags indicate whether any contributing monthly observation carries that flag. Their absence does not remove RMB's estimation qualification.

`fleet_normalized.sql` converts the daily rate to individual journeys by multiplying by 1,000 before dividing by licensed vehicles. Its output is **average daily journeys per licensed vehicle**, a descriptive ratio using administrative stock. It does not directly measure operational productivity, occupancy or actual daily deployment. RMB passenger estimation already uses licensed fleet information, so this ratio is not independent evidence of demand per vehicle.

The analysis pipeline cross-checks these queries against independently computed Pandas results. Tests in `tests/test_analysis_sql.py` exercise the queries through a read-only database connection, verify the denominator and baseline contracts, and confirm that the database remains unchanged. For standalone inspection with the SQLite command-line client, open the existing database in read-only mode and load a query:

```text
sqlite3 -readonly data/processed/transport.sqlite
.read sql/analysis/annual_ridership.sql
```

These commands require a separately installed SQLite client; the Python pipeline uses Python's built-in `sqlite3` module.

For portable inspection without that client, start `python` from the repository root
and run the following. The connection is read-only and closes after the query:

```python
from contextlib import closing
from pathlib import Path
import sqlite3
import pandas as pd

database = Path("data/processed/transport.sqlite").resolve()
query = Path("sql/analysis/annual_ridership.sql").read_text(encoding="utf-8")
with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as connection:
    print(pd.read_sql_query(query, connection).to_string(index=False))
```

Change only the query filename to inspect another existing analytical query. The
included database is sufficient for this read-only inspection; rebuilding it and
running the complete preparation/analysis test suite require the [official
specification download/checksum prerequisite](../../docs/data_reuse.md#download-the-dictionary-for-full-local-reproduction).
