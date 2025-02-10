import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import matplotlib.pyplot as plt

# Load the dataset
@st.cache_data
def load_crime_data():
    return pd.read_pickle('crime_data.pkl')

@st.cache_data
def load_location_data():
    return pd.read_pickle('state_district_lat_long.pkl')

crime_data = load_crime_data()
location_data = load_location_data()

crime_data['state/ut'] = crime_data['state/ut'].str.title()
crime_data['district'] = crime_data['district'].str.title()
location_data['State'] = location_data['State'].str.title()
location_data['District'] = location_data['District'].str.title()

# Crime Severity Score Calculation
crime_weights = {
    'murder': 5,
    'rape': 4,
    'kidnapping & abduction': 4,
    'robbery': 3,
    'burglary': 3,
    'dowry deaths': 3
}

def calculate_crime_severity(df):
    weighted_sum = sum(df[col].sum() * weight for col, weight in crime_weights.items())
    max_possible = sum(500 * weight for weight in crime_weights.values())
    crime_index = (weighted_sum / max_possible) * 100 if max_possible > 0 else 0
    return round(crime_index, 2)

# State Selection Page
def state_input_page():
    st.title("🌍 Crime Data Analysis & Safety Insights")
    state = st.selectbox('Select State/UT:', crime_data['state/ut'].unique())
    
    if st.button('Show Crime Severity Map'):
        if state:
            st.session_state.state = state
            st.session_state.page = 'CrimeAnalysisPage'
        else:
            st.warning("Please select a state.")

# Crime Analysis Page - Display Crime Severity for All Districts in State
def crime_analysis_page():
    st.title("🔍 Crime Data Analysis for Selected State")
    
    state = st.session_state.state
    filtered_data = crime_data[crime_data['state/ut'] == state]
    
    district_severity = {}
    trend_data = {}
    for district in filtered_data['district'].unique():
        district_data = filtered_data[filtered_data['district'] == district]
        district_severity[district] = calculate_crime_severity(district_data[district_data['year'] == 2024])
        trend_data[district] = {
            year: calculate_crime_severity(district_data[district_data['year'] == year])
            for year in [2022, 2023, 2024]
        }
    
    # Display Crime Severity Map
    st.subheader(f'Crime Severity Index for Districts in {state}')
    
    state_location = location_data[location_data['State'] == state]
    if not state_location.empty:
        latitude, longitude = state_location.iloc[0]['Latitude'], state_location.iloc[0]['Longitude']
        m = folium.Map(location=[latitude, longitude], zoom_start=7)

        for district, severity in district_severity.items():
            district_row = location_data[(location_data['State'] == state) & (location_data['District'] == district)]
            if not district_row.empty:
                lat, lon = district_row.iloc[0]['Latitude'], district_row.iloc[0]['Longitude']
                color = 'green' if severity < 25 else 'orange' if severity <= 55 else 'red'
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=10,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.7,
                    popup=f"{district}: {severity}"
                ).add_to(m)
        
        folium_static(m)
    else:
        st.warning("Coordinates for the selected state were not found.")
    
    # Crime Severity Table
    st.subheader("Crime Severity Index by District")
    df_severity = pd.DataFrame(district_severity.items(), columns=['District', 'Crime Severity Index']).sort_values(by='Crime Severity Index', ascending=False)
    st.dataframe(df_severity)

    # Recommendations for selected district
    selected_district = st.selectbox("Select a District for Detailed Analysis:", list(district_severity.keys()))
    crime_severity_index = district_severity[selected_district]
    st.metric(label="Crime Severity Index (Higher is riskier)", value=crime_severity_index)
    
    # Display Crime Severity Trend
    st.subheader("Crime Severity Trend (2022 - 2024)")
    st.line_chart(pd.DataFrame(trend_data[selected_district], index=["Crime Severity Index"]).T)
    
    if crime_severity_index < 25:
        st.markdown("<div class='success-alert'>🟢 This area is relatively safe.</div>", unsafe_allow_html=True)
    elif 25 <= crime_severity_index <= 55:
        st.markdown("<div class='warning-alert'>🟠 Moderate risk; stay cautious.</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='danger-alert'>🔴 High risk! Precaution is advised.</div>", unsafe_allow_html=True)

# Main code for app flow
if 'page' not in st.session_state:
    st.session_state.page = 'StateInputPage'

if st.session_state.page == 'StateInputPage':
    state_input_page()
elif st.session_state.page == 'CrimeAnalysisPage':
    crime_analysis_page()