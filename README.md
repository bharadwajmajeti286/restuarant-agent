# AI Restaurant Decision Agent

A simple Agentic AI project using Streamlit and live web search.

## Features
- Takes location, cuisine, dietary preference, budget, party size and distance constraints.
- Searches the live web for restaurant candidates.
- Ranks candidates with an explainable decision score.
- Recommends the best match and shows source links.
- No large restaurant database is required.

## Agent tools
- `search_restaurants()` — live web search.
- `rank_restaurants()` — multi-criteria ranking.
- `restaurant_agent()` — coordinates the tools.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit deployment
Upload `app.py`, `requirements.txt`, `README.md`, and `deployed_url.txt` to GitHub. Create a Streamlit Community Cloud app using `app.py` as the entry point.

## Demo queries
- Find a vegetarian restaurant near Hyderabad under ₹800 for two people.
- Find Indian food within 3 km and prefer highly rated places.
- I have ₹1,500 and want a family-friendly restaurant.

Web results change over time; verify important real-world details before visiting.
