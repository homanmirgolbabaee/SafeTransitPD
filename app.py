import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Document, Settings
from llama_index.llms.groq import Groq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import folium
from streamlit_folium import folium_static
import os
import json
from pathlib import Path
from telegram_bot import SafeTransitTelegramBot


# Initialize embedding model
def setup_embeddings():
    embed_model = HuggingFaceEmbedding(
        model_name="BAAI/bge-small-en-v1.5"
    )
    return embed_model

# Initialize Groq LLM
def init_llm():
    api_key = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
    if not api_key:
        st.warning("⚠️ No Groq API key found. Some features will be limited.")
        return None
    
    llm = Groq(
        api_key=api_key,
        model="mixtral-8x7b-32768",
        temperature=0.1,
        max_tokens=2048,
    )
    # Set as default LLM
    Settings.llm = llm
    return llm

# Create sample data
def create_sample_data():
    bus_stops = {
        "Stazione FS": (45.4184, 11.8801),
        "Prato della Valle": (45.3989, 11.8714),
        "Basilica del Santo": (45.4019, 11.8808),
        "Piazza delle Erbe": (45.4078, 11.8762),
        "Ospedale": (45.4109, 11.8888)
    }
    
    reports = pd.DataFrame({
        "location": list(bus_stops.keys()),
        "coordinates": list(bus_stops.values()),
        "timestamp": [datetime.now() - timedelta(minutes=x) for x in range(5)],
        "delay_minutes": [5, 10, 0, 15, 7],
        "crowd_level": ["Medium", "High", "Low", "Medium", "High"],
        "safety_score": [4.5, 3.8, 4.8, 4.2, 3.9]
    })
    
    return bus_stops, reports

# Initialize LlamaIndex with Groq
@st.cache_resource
def init_index():
    llm = init_llm()
    if not llm:
        return None
        
    embed_model = setup_embeddings()
    # Set as default embedding model
    Settings.embed_model = embed_model
    
    safety_docs = [
        Document(text="Common safety concerns in Padova transit include poor lighting at night and crowded buses during peak hours."),
        Document(text="Emergency procedures include immediate notification of authorities and trusted contacts."),
        Document(text="Bus line 10 connects Stazione FS to the University area with stops at major landmarks.")
    ]
    
    try:
        index = VectorStoreIndex.from_documents(
            safety_docs,
            llm=llm,
            embed_model=embed_model
        )
        return index
    except Exception as e:
        st.error(f"Error initializing index: {str(e)}")
        return None

def get_safety_recommendation(query_engine, location, time_of_day):
    if not query_engine:
        return "AI features are currently unavailable. Please check API configuration."
    
    try:
        query = f"What are the safety recommendations for traveling near {location} during {time_of_day}?"
        response = query_engine.query(query)
        return response.response
    except Exception as e:
        return f"Unable to get safety recommendations at this time: {str(e)}"

def calculate_safety_score(report_data):
    """Calculate safety score based on multiple factors"""
    base_score = 5.0
    modifiers = {
        "crowd_level": {
            "Low": 0,
            "Medium": -0.5,
            "High": -1.0
        },
        "safety_concerns": {
            "None": 0,
            "Poor Lighting": -1.0,
            "Suspicious Activity": -2.0,
            "Technical Issues": -0.5
        }
    }
    
    # Apply crowd level modifier
    score = base_score + modifiers["crowd_level"][report_data["crowd_level"]]
    
    # Apply safety concerns modifiers
    for concern in report_data["safety_concerns"]:
        if concern in modifiers["safety_concerns"]:
            score += modifiers["safety_concerns"][concern]
    
    # Ensure score stays within bounds
    return max(1.0, min(5.0, score))

def main():
    st.set_page_config(page_title="SafeTransit Padova", layout="wide")
    
    # Initialize session state
    if 'language' not in st.session_state:
        st.session_state.language = 'English'
    if 'emergency_mode' not in st.session_state:
        st.session_state.emergency_mode = False
    
    # Initialize LlamaIndex
    index = init_index()
    query_engine = index.as_query_engine(llm=Settings.llm) if index else None

    # Header with language selection
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("🚌 SafeTransit Padova")
    with col2:
        st.session_state.language = st.selectbox(
            "Language/Lingua",
            ["English", "Italiano"],
            index=0
        )
    
    tabs = st.tabs(["Real-time Map", "Report Update", "Safety Features"])
    bus_stops, reports = create_sample_data()
    # Get Telegram token from secrets
    telegram_token = st.secrets.get("TELEGRAM_BOT_TOKEN", os.getenv("TELEGRAM_BOT_TOKEN", ""))
    # Start Telegram bot in a separate thread if token is available

    if telegram_token:
        bot = SafeTransitTelegramBot(telegram_token, bus_stops, query_engine)
        import threading
        bot_thread = threading.Thread(target=bot.run, daemon=True)
        bot_thread.start()
        st.success("🤖 Telegram bot is running! Search for @SafeTransitPadovaBot on Telegram.")
    else:
        st.warning("⚠️ Telegram bot token not found. Bot features are disabled.")
    # Initialize bus stops and reports


    
    # Real-time Map Tab
    with tabs[0]:
        st.subheader("Real-time Transit Map")
        
        # Create map centered on Padova
        m = folium.Map(location=[45.4064, 11.8768], zoom_start=14)
        
        # Add markers for each bus stop
        for name, coords in bus_stops.items():
            report = reports[reports['location'] == name].iloc[0]
            color = 'green' if report['safety_score'] >= 4.5 else 'orange' if report['safety_score'] >= 4.0 else 'red'
            
            popup_text = f"""
            <b>{name}</b><br>
            Delay: {report['delay_minutes']} mins<br>
            Crowd: {report['crowd_level']}<br>
            Safety Score: {report['safety_score']}/5.0
            """
            
            folium.Marker(
                coords,
                popup=popup_text,
                icon=folium.Icon(color=color)
            ).add_to(m)
        
        folium_static(m)
        
        st.subheader("Latest Updates")
        st.dataframe(
            reports[['location', 'timestamp', 'delay_minutes', 'crowd_level', 'safety_score']]
        )
        
        # AI Safety Insights
        if st.button("Get AI Safety Insights") and query_engine:
            current_time = datetime.now().strftime("%H:%M")
            with st.spinner("Analyzing safety patterns..."):
                insight = get_safety_recommendation(
                    query_engine,
                    "Padova city center",
                    current_time
                )
                st.info(f"🤖 AI Safety Insight: {insight}")
    
    # Report Update Tab
    with tabs[1]:
        st.subheader("Submit Transit Update")
        
        col1, col2 = st.columns(2)
        with col1:
            location = st.selectbox("Location", list(bus_stops.keys()))
            delay = st.number_input("Delay (minutes)", min_value=0, max_value=60, value=0)
            crowd = st.select_slider(
                "Crowd Level",
                options=["Low", "Medium", "High"],
                value="Medium"
            )
        
        with col2:
            safety_concerns = st.multiselect(
                "Safety Concerns",
                ["None", "Poor Lighting", "Suspicious Activity", "Technical Issues"]
            )
            
            additional_info = st.text_area("Additional Information")
            
            if st.button("Submit Report"):
                report_data = {
                    "location": location,
                    "delay_minutes": delay,
                    "crowd_level": crowd,
                    "safety_concerns": safety_concerns,
                    "additional_info": additional_info,
                    "timestamp": datetime.now().isoformat(),
                }
                
                # Calculate safety score
                report_data["safety_score"] = calculate_safety_score(report_data)
                
                if query_engine:
                    with st.spinner("Analyzing report..."):
                        analysis = query_engine.query(
                            f"Analyze this safety report: Location: {location}, "
                            f"Crowd Level: {crowd}, Safety Concerns: {', '.join(safety_concerns)}"
                        ).response
                        st.success("Report submitted successfully! Thank you for contributing to safer transit.")
                        st.info(f"🤖 AI Analysis: {analysis}")
                else:
                    st.success("Report submitted successfully! Thank you for contributing to safer transit.")
    
    # Safety Features Tab
    with tabs[2]:
        st.subheader("Safety Features")
        
        # Emergency Button
        if st.button("🚨 EMERGENCY BUTTON", use_container_width=True):
            st.session_state.emergency_mode = True
        
        if st.session_state.emergency_mode:
            with st.spinner("Activating emergency response..."):
                emergency_response = query_engine.query(
                    "What are the immediate steps to take in a transit emergency?"
                ).response if query_engine else "Alerting emergency services..."
                
                st.error(f"""
                Emergency Mode Activated!
                {emergency_response}
                1. Alerting nearby safety personnel
                2. Notifying trusted contacts
                3. Recording location data
                """)
                if st.button("Cancel Emergency"):
                    st.session_state.emergency_mode = False
        
        # Safe Route Planning
        st.subheader("Plan Safe Route")
        col1, col2 = st.columns(2)
        with col1:
            start = st.selectbox("From", list(bus_stops.keys()))
        with col2:
            end = st.selectbox("To", list(bus_stops.keys()))
            
        if st.button("Find Safest Route"):
            with st.spinner("Calculating safest route..."):
                route_recommendation = query_engine.query(
                    f"Suggest the safest route from {start} to {end} in Padova, "
                    "considering current time and safety scores"
                ).response if query_engine else "Calculating optimal route based on safety scores..."
                st.info(f"🤖 Recommended Route:\n{route_recommendation}")

if __name__ == "__main__":
    main()