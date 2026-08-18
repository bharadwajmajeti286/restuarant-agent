import re
import streamlit as st
from ddgs import DDGS

st.set_page_config(page_title="AI Restaurant Decision Agent", page_icon="🍽️", layout="wide")

def search_restaurants(location, cuisine, budget, dietary, open_now=False):
    """Tool 1: search the live web for restaurant candidates."""
    query = f"{cuisine} restaurants in {location} {dietary} under {budget} rupees"
    if open_now:
        query += " open now"
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=8)), None
    except Exception as e:
        return [], str(e)

def money_score(text, budget):
    nums = [int(x.replace(",", "")) for x in re.findall(r"(?:₹|Rs\.?|INR)\s*([0-9][0-9,]*)", text, re.I)]
    return 0.6 if not nums else max(0.0, min(1.0, budget / max(min(nums), 1)))

def rating_score(text):
    vals = [float(x) for x in re.findall(r"\b([1-5](?:\.[0-9])?)\s*(?:/5|stars?)\b", text, re.I)]
    return 0.65 if not vals else min(max(vals[0] / 5, 0), 1)

def distance_score(text, max_distance):
    vals = [float(x) for x in re.findall(r"\b([0-9]+(?:\.[0-9]+)?)\s*km\b", text, re.I)]
    return 0.6 if not vals else max(0.0, min(1.0, 1 - vals[0] / max(max_distance, 1)))

def preference_score(text, cuisine, dietary):
    t = text.lower()
    score = 0.5
    if cuisine.lower() in t: score += 0.25
    if dietary.lower() in t: score += 0.25
    return min(score, 1.0)

def rank_restaurants(results, cuisine, dietary, budget, max_distance):
    """Tool 2: rank candidates using multiple user constraints."""
    ranked = []
    for r in results:
        title = r.get("title", "Restaurant")
        body = r.get("body", "")
        combined = f"{title}. {body}"
        score = (
            0.30 * money_score(combined, budget)
            + 0.25 * rating_score(combined)
            + 0.20 * distance_score(combined, max_distance)
            + 0.25 * preference_score(combined, cuisine, dietary)
        )
        ranked.append({"name": title, "description": body, "url": r.get("href", ""), "score": round(score * 10, 1)})
    return sorted(ranked, key=lambda x: x["score"], reverse=True)

def restaurant_agent(location, cuisine, budget, dietary, max_distance, open_now):
    """Agent: decides to search, rank and recommend."""
    results, error = search_restaurants(location, cuisine, budget, dietary, open_now)
    if error:
        return [], error
    return rank_restaurants(results, cuisine, dietary, budget, max_distance), None

st.title("🍽️ AI Restaurant Decision Agent")
st.write("A web-powered agent that searches current restaurant information, compares options, and recommends the best match.")

with st.sidebar:
    st.header("Your requirements")
    location = st.text_input("Location", "Hyderabad")
    cuisine = st.text_input("Cuisine", "Indian")
    dietary = st.text_input("Dietary preference", "vegetarian")
    budget = st.number_input("Budget (₹)", min_value=100, max_value=50000, value=1000, step=100)
    people = st.number_input("Number of people", min_value=1, max_value=20, value=2)
    max_distance = st.slider("Maximum distance (km)", 1, 30, 5)
    open_now = st.checkbox("Prefer restaurants open now")

request = st.text_area("What do you want?", "Find the best restaurant for me based on my requirements.")

if st.button("🔎 Find & Decide", type="primary"):
    with st.spinner("Agent is searching the live web and comparing restaurants..."):
        ranked, error = restaurant_agent(location, cuisine, budget, dietary, max_distance, open_now)

    if error:
        st.error(f"Web search failed: {error}")
    elif not ranked:
        st.warning("No results found. Try a broader location or cuisine.")
    else:
        best = ranked[0]
        st.success(f"🏆 Recommended: {best['name']} — Decision score {best['score']}/10")
        st.markdown("### Why this was selected")
        st.write(f"The agent ranked this option using your {cuisine} preference, {dietary} requirement, ₹{budget:,} budget and {max_distance} km limit. The score combines budget, rating evidence, distance evidence and preference matching.")
        st.markdown("### Top options")
        for i, item in enumerate(ranked[:5], 1):
            st.markdown(f"#### {i}. {item['name']} — {item['score']}/10")
            st.write(item["description"])
            if item["url"]:
                st.markdown(f"[View source]({item['url']})")

st.divider()
st.caption("Agent flow: search_restaurants → rank_restaurants → recommendation. Verify price, availability and opening hours before visiting.")

with st.expander("Example requests"):
    st.write("• Find a vegetarian restaurant near Hyderabad under ₹800 for two people.")
    st.write("• Find Indian food within 3 km and prefer highly rated places.")
    st.write("• I have ₹1,500 and want a family-friendly restaurant.")
