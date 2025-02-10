import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

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

# Machine Learning Model for Crime Hotspot Prediction
def train_model():
    crime_data['severity_index'] = crime_data.apply(lambda x: calculate_crime_severity(pd.DataFrame([x])), axis=1)
    
    features = ['year', 'state/ut', 'district'] + list(crime_weights.keys())
    label_encoder = LabelEncoder()
    crime_data['state/ut'] = label_encoder.fit_transform(crime_data['state/ut'])
    crime_data['district'] = label_encoder.fit_transform(crime_data['district'])
    
    X = crime_data[features]
    y = (crime_data['severity_index'] > 50).astype(int)  # 1 for hotspot, 0 for non-hotspot
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    return model, label_encoder

model, label_encoder = train_model()

def predict_hotspots(state, district):
    state_encoded = label_encoder.transform([state])[0]
    district_encoded = label_encoder.transform([district])[0]
    
    latest_year = crime_data['year'].max()
    input_data = [[latest_year, state_encoded, district_encoded] + [crime_data[col].mean() for col in crime_weights.keys()]]
    prediction = model.predict(input_data)[0]
    return 'Hotspot' if prediction == 1 else 'Safe Zone'

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
    
    # Display Crime Severity Table
    st.subheader("Crime Severity Index by District")
    df_severity = pd.DataFrame(district_severity.items(), columns=['District', 'Crime Severity Index']).sort_values(by='Crime Severity Index', ascending=False)
    st.dataframe(df_severity)
    
    # Predict and Display Hotspot Status with Recommendations
    selected_district = st.selectbox("Select a District for Detailed Analysis:", list(district_severity.keys()))
    crime_severity_index = district_severity[selected_district]
    st.metric(label="Crime Severity Index (Higher is riskier)", value=crime_severity_index)
    
    if crime_severity_index < 25:
        st.markdown("<div class='success-alert'>🟢 This area is relatively safe.</div>", unsafe_allow_html=True)
        st.write("### Recommendations for Safe Zones:")
        st.write("1. Maintain neighborhood watch programs to keep the community engaged.")
        st.write("2. Increase public awareness through safety workshops.")
        st.write("3. Foster community partnerships with local law enforcement.")
    elif 25 <= crime_severity_index <= 55:
        st.markdown("<div class='warning-alert'>🟠 Moderate risk; stay cautious.</div>", unsafe_allow_html=True)
        st.write("### Recommendations for Moderate Risk Zones:")
        st.write("1. Install additional street lighting in dark spots.")
        st.write("2. Organize community patrols in higher crime areas.")
        st.write("3. Encourage establishing local security services.")
    else:
        st.markdown("<div class='danger-alert'>🔴 High risk! Precaution is advised.</div>", unsafe_allow_html=True)
        st.write("### Recommendations for High-Risk Zones:")
        st.write("1. Increase law enforcement presence in hotspot areas.")
        st.write("2. Establish neighborhood vigilance programs.")
        st.write("3. Launch emergency response systems with real-time alerts.")
    
    # Display Crime Severity Trend
    st.subheader("Crime Severity Trend (2022 - 2024)")
    st.line_chart(pd.DataFrame(trend_data[selected_district], index=["Crime Severity Index"]).T)

# Main code for app flow
if 'page' not in st.session_state:
    st.session_state.page = 'StateInputPage'

if st.session_state.page == 'StateInputPage':
    state_input_page()
elif st.session_state.page == 'CrimeAnalysisPage':
    crime_analysis_page()