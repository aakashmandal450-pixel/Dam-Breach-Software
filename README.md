# Dam Breach Studio

A first prototype for a graphical dam breach and GLOF analysis tool.

This version focuses on the first useful workflow:

- choose a breach scenario
- enter basic dam/reservoir/lake data
- calculate breach parameters with empirical equations
- estimate glacial lake volume when bathymetry is unavailable
- generate a simple outflow hydrograph
- show diagrams and simple explanations
- export hydrograph results as CSV

The application is intentionally transparent: every calculation should explain what it is doing,
where it is suitable, and where it is uncertain.

## Recommended Way To Run In VS Code

1. Open this folder in VS Code:

   ```powershell
   D:\Dam Breach Software
   ```

2. Create a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

4. Run the app:

   ```powershell
   streamlit run app\main.py
   ```

5. Open the local URL shown by Streamlit, usually:

   ```text
   http://localhost:8501
   ```

## Project Structure

```text
app/
  main.py              Streamlit user interface
  diagrams.py          Simple educational diagrams
models/
  breach_equations.py  Empirical breach parameter methods
  lake_volume.py       Glacial lake volume-area estimators
  hydrograph.py        Simple hydrograph generation
  scenarios.py         Scenario definitions and guidance
tests/
  test_models.py       Basic calculation checks
```

## Important Note

This is not yet a validated engineering tool. It is a research and learning prototype.
Before using results for real safety decisions, every method must be checked against original
papers, manuals, and observed case studies.
