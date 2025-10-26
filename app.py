import streamlit as st
import pandas as pd
import pydeck as pdk
import time

# --- Page Configuration ---
st.set_page_config(
    page_title="India Safety Dashboard",
    page_icon="🇮🇳",
    layout="wide"
)

# --- Custom CSS for Elegance ---
# Added background-color to the main app container
st.markdown("""
<style>
    /* --- Main Background Color --- */
    [data-testid="stAppViewContainer"] {
        background-color: #f0f2f6; /* Subtle light gray background */
    }

    /* --- Card Styling (Containers) --- */
    [data-testid="stVerticalBlockBorder"] {
        background-color: #ffffff; /* Make cards white for contrast */
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        padding: 1.25rem; 
    }
    
    /* --- KPI Metric Styling --- */
    [data-testid="stMetric"] {
        background-color: #f8f9fa; /* Light grey background for metrics */
        border-radius: 10px;
        padding: 1rem;
    }

    /* --- Spacing --- */
    [data-testid="stAppViewContainer"] > .main > div:nth-child(1) {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)


# --- Data Loading ---
DATA_FILE = "hazards.csv"

# Function to load data, with caching
@st.cache_data
def load_data():
    try:
        df = pd.read_csv(DATA_FILE)
        # Convert timestamp to datetime objects
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except FileNotFoundError:
        # If file not found, return an empty dataframe with correct columns
        st.error(f"Error: '{DATA_FILE}' not found. A new one will be created when you add a report.")
        return pd.DataFrame(columns=['lat', 'lon', 'hazard_type', 'severity', 'status', 'reported_by', 'timestamp'])

# Load the data
df = load_data()

# --- Helper Function to Save Data ---
def save_data(dataframe):
    dataframe.to_csv(DATA_FILE, index=False)
    # Clear the cache so st.cache_data will rerun
    st.cache_data.clear()

# --- Helper Function for Dataframe Styling ---
def style_severity(row):
    severity = row['severity']
    if severity == 'Critical':
        return ['background-color: #ffadad'] * len(row) # Light Red
    elif severity == 'High':
        return ['background-color: #ffd6a5'] * len(row) # Light Orange
    elif severity == 'Medium':
        return ['background-color: #fdffb6'] * len(row) # Light Yellow
    else:
        return [''] * len(row) # Default

# --- Sidebar: User Input Form ---
st.sidebar.header("Report a New Hazard")
with st.sidebar.form(key="hazard_form", clear_on_submit=True):
    st.write("Submit a new incident report.")
    
    hazard_type = st.selectbox(
        "Hazard Type",
        ["Fire", "Chemical Leak", "Equipment Failure", "Structural Risk", "Other"]
    )
    severity = st.select_slider(
        "Severity",
        options=["Low", "Medium", "High", "Critical"],
        value="Medium"
    )
    # Use Indian coordinates as a sensible default
    lat = st.number_input("Latitude", format="%.6f", value=20.5937)
    lon = st.number_input("Longitude", format="%.6f", value=78.9629)
    reported_by = st.text_input("Reported By (e.g., 'Worker A', 'Safety Officer')")
    
    submit_button = st.form_submit_button(label="Submit Report")

    if submit_button:
        if not reported_by or not lat or not lon:
            st.sidebar.error("Please fill in all fields.")
        else:
            # Create a new report as a DataFrame
            new_report = pd.DataFrame([{
                "lat": lat,
                "lon": lon,
                "hazard_type": hazard_type,
                "severity": severity,
                "status": "Active",  # New reports are always 'Active'
                "reported_by": reported_by,
                "timestamp": pd.Timestamp.now()
            }])
            
            # Append the new report to the main dataframe
            df = pd.concat([df, new_report], ignore_index=True)
            
            # Save the updated dataframe to the CSV
            save_data(df)
            
            st.sidebar.success("Hazard reported successfully!")
            st.toast("Dashboard refreshing...")
            time.sleep(1)
            # Rerun the script to show the new data
            st.rerun()

# --- Main Dashboard ---
st.title("🇮🇳 India Safety Dashboard: Real-time Hazard Monitoring")
st.write("This dashboard provides a real-time overview of reported industrial hazards across sites.")

# --- KPIs (Key Performance Indicators) ---
# We wrap this section in a container to create a "card"
with st.container(border=True):
    st.subheader("📈 Dashboard Overview")
    
    col1, col2, col3 = st.columns(3)
    total_reports = len(df)
    active_incidents = len(df[df['status'] == 'Active'])
    high_severity = len(df[df['severity'].isin(['High', 'Critical'])])

    col1.metric("Total Reports", total_reports)
    col2.metric("Active Incidents", active_incidents)
    col3.metric("High/Critical Severity", high_severity)

st.divider() # Use a clean divider

# --- Visualizations: Map and Bar Charts ---
st.subheader("📊 Hazard Analysis")

col_map, col_chart = st.columns([2, 1])  # Make the map wider

with col_map:
    # Wrap map in its own card
    with st.container(border=True):
        st.subheader("🗺️ Hazard Distribution Map")
        if df.empty:
            st.warning("No data to display on map. Please submit a report.")
        else:
            # Set the view for the map, centered on India
            view_state = pdk.ViewState(
                latitude=20.5937,
                longitude=78.9629,
                zoom=4,
                pitch=50,
            )

            # Create a Pydeck layer
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position="[lon, lat]",
                get_fill_color="""
                    severity == 'Critical' ? [255, 0, 0] : 
                    severity == 'High' ? [255, 140, 0] : 
                    severity == 'Medium' ? [255, 255, 0] : [0, 128, 0]
                """,
                get_radius=50000,  # Radius in meters
                pickable=True,
                auto_highlight=True
            )

            # Tooltip
            tooltip = {
                "html": """
                    <b>Hazard:</b> {hazard_type}<br/>
                    <b>Severity:</b> {severity}<br/>
                    <b>Status:</b> {status}<br/>
                    <b>Reported by:</b> {reported_by}
                """,
                "style": {"backgroundColor": "steelblue", "color": "white"}
            }

            # Render the map
            st.pydeck_chart(pdk.Deck(
                map_style="mapbox://styles/mapbox/light-v9",
                initial_view_state=view_state,
                layers=[layer],
                tooltip=tooltip
            ))

with col_chart:
    # Wrap each chart in its own card for a clean, stacked look
    with st.container(border=True):
        st.subheader("By Type")
        if not df.empty:
            st.bar_chart(df['hazard_type'].value_counts())
        else:
            st.info("No data for bar chart.")

    st.write("") # Add some vertical space

    with st.container(border=True):
        st.subheader("By Severity")
        if not df.empty:
            st.bar_chart(df['severity'].value_counts())
        else:
            st.info("No data for bar chart.")

st.divider()

# --- Raw Data Table ---
# Wrap the data table in its own card
with st.container(border=True):
    st.subheader("🗃️ All Reported Incidents")
    st.write("View all submitted reports. The most recent reports are at the top.")
    if not df.empty:
        # Sort by timestamp
        sorted_df = df.sort_values(by="timestamp", ascending=False)
        
        # Apply the styling function
        st.dataframe(
            sorted_df.style.apply(style_severity, axis=1),
            use_container_width=True
        )
    else:
        st.info("No reports submitted yet.")