import streamlit as st
import pandas as pd
import folium
import matplotlib.pyplot as plt
from streamlit_folium import folium_static

# Load the datasets
@st.cache_data
def load_crime_data():
    return pd.read_pickle('crime_data.pkl')

@st.cache_data
def load_location_data():
    return pd.read_pickle('state_district_lat_long.pkl')

crime_data = load_crime_data()
location_data = load_location_data()

# Capitalize state and district names for consistency
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
    'burglary': 2,
    'dowry deaths': 3
}

def calculate_crime_severity(df):
    weighted_sum = sum(df[col].sum() * weight for col, weight in crime_weights.items())
    max_possible = sum(df[col].max() * weight for col, weight in crime_weights.items())
    crime_index = (weighted_sum / max_possible) * 100  # Normalize to a 0-100 scale
    return round(crime_index, 2)

# Main app flow
if 'page' not in st.session_state:
    st.session_state.page = 'Home'

# Home page - State and District selection
if st.session_state.page == 'Home':
    st.title('🌍 Crime Data Analysis & Safety Insights')

    state = st.selectbox('Select State/UT:', crime_data['state/ut'].unique())

    districts = crime_data[crime_data['state/ut'] == state]['district'].unique()
    district = st.selectbox('Select District:', districts)

    if st.button('Show Crime Data'):
        st.session_state.state = state
        st.session_state.district = district
        st.session_state.page = 'CrimeData'

# Crime Data Page - Display insights and analysis
if st.session_state.page == 'CrimeData':
    state = st.session_state.state
    district = st.session_state.district

    filtered_data = crime_data[
        (crime_data['state/ut'] == state) &
        (crime_data['district'] == district) & 
        (crime_data['year'].isin([2023, 2024]))
    ]

    st.subheader(f'Crime Data for {district}, {state}')

    # Crime Severity Index
    crime_severity_index = calculate_crime_severity(filtered_data)
    st.metric(label="Crime Severity Index (Higher is riskier)", value=crime_severity_index)

    if crime_severity_index < 40:
        st.success("🟢 This area is relatively safe.")
    elif crime_severity_index < 70:
        st.warning("🟠 Moderate risk; stay cautious.")
    else:
        st.error("🔴 High risk! Precaution is advised.")

    # Crime Frequency Analysis
    st.subheader('Crime Distribution')
    crime_types = ['murder', 'rape', 'kidnapping & abduction', 'robbery', 'burglary', 'dowry deaths']
    crime_frequencies = filtered_data[crime_types].sum().sort_values(ascending=False)
    st.bar_chart(crime_frequencies)

    # Crime Trend Visualization (2021-2024)
    st.subheader('Crime Trends Over the Years')
    trend_data = crime_data[(crime_data['state/ut'] == state) & (crime_data['district'] == district) & (crime_data['year'].isin([2021, 2022, 2023, 2024]))]

    plt.figure(figsize=(10, 6))
    for crime in crime_types:
        crime_sum_by_year = trend_data.groupby('year')[crime].sum()
        plt.plot(crime_sum_by_year.index, crime_sum_by_year.values, label=crime)

    plt.title(f'Crime Trends for {district}, {state} (2021-2024)')
    plt.xlabel('Year')
    plt.ylabel('Crime Count')
    plt.legend(title="Crime Types")
    st.pyplot(plt)

    # Safety Recommendations
    st.subheader('Safety Recommendations')
    if crime_frequencies['murder'] > 50:
        st.warning("🔴 Avoid high-crime areas at night and stay vigilant.")
    if crime_frequencies['rape'] > 30:
        st.warning("⚠️ Travel in groups and use verified transport services.")
    if crime_frequencies['burglary'] > 100:
        st.warning("🏠 Install security systems and inform neighbors when away.")

    # Interactive Crime Hotspot Map
    st.subheader('Crime Hotspot Map')
    m = folium.Map(location=[filtered_data['latitude'].mean(), filtered_data['longitude'].mean()], zoom_start=10)

    # Position map control on the left side by setting position to 'topleft'
    folium.LayerControl(position='topleft').add_to(m)

    for idx, row in filtered_data.iterrows():
        folium.Marker([row['latitude'], row['longitude']], popup=f"Crime: {row['murder']} Murders").add_to(m)
    
    folium_static(m)

    # Back Button
    if st.button('Go Back'):
        st.session_state.page = 'Home'

