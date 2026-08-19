import os,re
import streamlit as st
from ddgs import DDGS
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq

st.set_page_config(page_title="AI Restaurant Decision Agent", page_icon="🍽️", layout="wide")

class State(TypedDict, total=False):
    location:str
    cuisine:str
    budget:int
    dietary:str
    max_distance:int
    open_now:bool
    results:list
    ranked:list
    answer:str
    error:str

def search_restaurants(state):
    query=f"{state['cuisine']} restaurants in {state['location']} {state['dietary']} under {state['budget']} rupees"
    if state["open_now"]: query += " open now"
    try:
        with DDGS() as ddgs:
            results=list(ddgs.text(query,max_results=8))
        return {"results":results}
    except Exception as e:
        return {"results":[],"error":str(e)}

def money_score(text,budget):
    nums=[int(x.replace(",","")) for x in re.findall(r"(?:₹|Rs\.?|INR)\s*([0-9][0-9,]*)",text,re.I)]
    return 0.6 if not nums else max(0.0,min(1.0,budget/max(min(nums),1)))

def rating_score(text):
    vals=[float(x) for x in re.findall(r"\b([1-5](?:\.[0-9])?)\s*(?:/5|stars?)\b",text,re.I)]
    return 0.65 if not vals else min(max(vals[0]/5,0),1)

def distance_score(text,max_distance):
    vals=[float(x) for x in re.findall(r"\b([0-9]+(?:\.[0-9]+)?)\s*km\b",text,re.I)]
    return 0.6 if not vals else max(0.0,min(1.0,1-vals[0]/max(max_distance,1)))

def preference_score(text,cuisine,dietary):
    t=text.lower(); score=.5
    if cuisine.lower() in t: score+=.25
    if dietary.lower() in t: score+=.25
    return min(score,1)

def rank_restaurants(state):
    ranked=[]
    for r in state.get("results",[]):
        name=r.get("title","Restaurant"); body=r.get("body","")
        text=f"{name}. {body}"
        score=(.30*money_score(text,state["budget"])+.25*rating_score(text)+
               .20*distance_score(text,state["max_distance"])+
               .25*preference_score(text,state["cuisine"],state["dietary"]))
        ranked.append({"name":name,"description":body,"url":r.get("href",""),
                       "score":round(score*10,1)})
    return {"ranked":sorted(ranked,key=lambda x:x["score"],reverse=True)}

def llm_decide(state):
    ranked=state.get("ranked",[])
    if not ranked: return {"answer":"I could not find suitable restaurants. Try a broader search."}
    api_key=os.getenv("GROQ_API_KEY")
    if not api_key:
        return {"answer":f"Recommended: {ranked[0]['name']} — score {ranked[0]['score']}/10.\n\nLLM is not connected yet. Add GROQ_API_KEY to enable the AI explanation."}
    llm=ChatGroq(model="llama-3.1-8b-instant",temperature=0.2,api_key=api_key)
    top=ranked[:5]
    prompt=f"""You are a simple restaurant decision assistant.
User wants: {state['cuisine']} food, {state['dietary']}, budget ₹{state['budget']}, within {state['max_distance']} km.
Candidates:
{json.dumps(top,ensure_ascii=False)}
Choose the best candidate using the scores and available evidence. Give a short recommendation and 2 reasons. Do not invent facts."""
    return {"answer":llm.invoke(prompt).content}

def build_graph():
    g=StateGraph(State)
    g.add_node("search",search_restaurants)
    g.add_node("rank",rank_restaurants)
    g.add_node("decide",llm_decide)
    g.add_edge(START,"search"); g.add_edge("search","rank"); g.add_edge("rank","decide"); g.add_edge("decide",END)
    return g.compile()

graph=build_graph()

st.title("🍽️ AI Restaurant Decision Agent")
st.write("LangGraph + LangChain LLM + live web search + simple ranking.")

with st.sidebar:
    st.header("Your requirements")
    location=st.text_input("Location","Hyderabad")
    cuisine=st.text_input("Cuisine","Indian")
    dietary=st.text_input("Dietary preference","vegetarian")
    budget=st.number_input("Budget (₹)",100,50000,1000,100)
    people=st.number_input("Number of people",1,20,2)
    max_distance=st.slider("Maximum distance (km)",1,30,5)
    open_now=st.checkbox("Prefer restaurants open now")

request=st.text_area("What do you want?","Find the best restaurant for me based on my requirements.")

if st.button("🔎 Find & Decide",type="primary"):
    with st.spinner("LangGraph is running the search → ranking → LLM decision flow..."):
        state=graph.invoke({"location":location,"cuisine":cuisine,"budget":budget,
                            "dietary":dietary,"max_distance":max_distance,
                            "open_now":open_now})
    if state.get("error"): st.error(state["error"])
    else:
        ranked=state.get("ranked",[])
        st.success(state.get("answer","No recommendation."))
        st.markdown("### Top options")
        for i,item in enumerate(ranked[:5],1):
            st.markdown(f"**{i}. {item['name']} — {item['score']}/10**")
            st.write(item["description"])
            if item["url"]: st.markdown(f"[View source]({item['url']})")
st.caption("Simple agent flow: LangGraph → web search → ranking → LLM decision.")
