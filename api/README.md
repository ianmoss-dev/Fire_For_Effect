# FIRE for Effect API

This package will hold the FastAPI backend and pure calculation modules for the rebuild.

Current status:

- Data loading extracted from the Streamlit app
- Base pay lookup extracted
- BAS lookup extracted
- BAH lookup extracted
- OHA lookup extracted
- Combined CONUS/OCONUS income calculation extracted
- First FastAPI endpoint added at `POST /income/calculate`
- Retirement savings-rate endpoint added at `POST /retirement/solve-savings-rate`
- Monte Carlo endpoint added at `POST /retirement/monte-carlo`
- Budget summary endpoint added at `POST /budget/summary`
- Promotion timeline logic extracted
- High-3 pension calculation extracted
- TSP fund assumptions and lifecycle allocation extracted
- Savings-rate solver extracted
- First parity tests added

Run tests from the repo root:

```powershell
python -m unittest discover -s api\tests -v
```

Set up local API dependencies:

```powershell
cd api
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
```

Run tests with the local API environment:

```powershell
.\.venv\Scripts\python -m unittest discover -s tests -v
```

Run the API locally:

```powershell
uvicorn app.main:app --reload
```
