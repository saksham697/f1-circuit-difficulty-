# 🏁 F1 Circuit Difficulty Profile — Streamlit App

Interactive dark-themed web app: a world map with every circuit's **real track
outline**, click a circuit to see its difficulty profile (chaos score, DNF rate,
pole-to-win, grid→finish correlation), plus ranked charts and a sortable table.

The heavy lifting already happened upstream in the MySQL analytics pipeline —
this app reads the pre-computed results from `app_data.json`, so it runs anywhere
with **no database and no network** needed.

---

## Run it locally

```bash
pip install -r requirements.txt
streamlit run app.py
```
It opens at http://localhost:8501.

---

## Deploy it free (Streamlit Community Cloud)

1. **Put this folder in a GitHub repo.** It needs exactly these files:
   ```
   app.py
   app_data.json
   requirements.txt
   .streamlit/config.toml
   ```
2. Go to **https://share.streamlit.io** and sign in with GitHub.
3. **New app** → pick your repo, branch `main`, main file `app.py` → **Deploy**.
4. Wait ~2 minutes. You get a public URL like
   `https://your-name-f1-circuits.streamlit.app` — put it on your resume.

That's it. Every push to the repo auto-redeploys.

---

## How the data gets here (the story for interviews)

```
CSV / jolpica API  ->  MySQL schema  ->  SQL views (v_circuit_profile)
        ->  merge with track-outline GeoJSON  ->  app_data.json  ->  this app
```

The app is the *storefront*; the MySQL + SQL work is the *engine*. To refresh
after new races: re-run the pipeline in the main project, regenerate
`app_data.json` (the merge script lives in the main project), and push.

---

## Credits / data
- Race results: Ergast-derived dataset + jolpica-f1 API (2025+).
- Track outlines: [bacinger/f1-circuits](https://github.com/bacinger/f1-circuits)
  (GeoJSON, matched to circuits by coordinates — all 26 matched cleanly).
- Not affiliated with or endorsed by Formula 1. F1 marks belong to
  Formula One Licensing B.V.
