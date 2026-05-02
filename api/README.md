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
- First parity tests added

Run tests from the repo root:

```powershell
python -m unittest discover -s api\tests -v
```

Run the API locally after installing API dependencies:

```powershell
cd api
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```
