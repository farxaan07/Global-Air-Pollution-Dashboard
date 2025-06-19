import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px

# -------------------------------
# Configuration and Styling
# -------------------------------
st.set_page_config(page_title="Global Air Pollution Dashboard", layout="wide")

def apply_custom_css():
    """Inject custom CSS for header and animations."""
    st.markdown("""
        <style>
            .main-title {
                font-size: 3em;
                font-weight: 800;
                text-align: center;
                background: linear-gradient(to right, deepskyblue, steelblue);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                animation: fadeIn 1.5s ease-in-out;
                margin-bottom: 0.2em;
            }

            .subheading-box {
                background-color: #f0f9ff;
                border-left: 6px solid #1e90ff;
                padding: 10px 20px;
                margin: 0 auto 30px auto;
                width: fit-content;
                border-radius: 8px;
                font-size: 1.2em;
                font-weight: 500;
                color: #003366;
                text-align: center;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            }

            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(-10px); }
                to { opacity: 1; transform: translateY(0); }
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-title"> Global Air Pollution Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="subheading-box">Tracking Global Air Quality for a Healthier Tomorrow</div>', unsafe_allow_html=True)

# -------------------------------
# Data Loading and Merging
# -------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv('cleaned_global_air_pollution.csv')
    cities_df = pd.read_csv('worldcities.csv')

    df['City'] = df['City'].str.strip().str.title()
    df['Country'] = df['Country'].str.strip().str.title()
    cities_df['city'] = cities_df['city'].str.strip().str.title()
    cities_df['country'] = cities_df['country'].str.strip().str.title()

    return pd.merge(df, cities_df, left_on=['City', 'Country'], right_on=['city', 'country'], how='left')

# -------------------------------
# Filters
# -------------------------------
def connected_filters(data):
    st.markdown("### Connected Visualisations")
    col1, col2 = st.columns(2)
    countries = sorted(data['Country'].dropna().unique())
    selected_countries = col1.multiselect("Select Countries", countries, default=[countries[0]])
    selected_pollutant = col2.selectbox("Select Pollutant", ['CO AQI Value', 'Ozone AQI Value', 'NO2 AQI Value', 'PM2.5 AQI Value'])

    min_val, max_val = float(data[selected_pollutant].min()), float(data[selected_pollutant].max())
    selected_range = st.slider(f"Select Range for {selected_pollutant}", 0.0, round(max_val, 2), (0.0, round(max_val, 2)))

    df_filtered = data[(data['Country'].isin(selected_countries)) &
                       (data[selected_pollutant] >= selected_range[0]) &
                       (data[selected_pollutant] <= selected_range[1])]

    return df_filtered, selected_countries, selected_pollutant

# -------------------------------
# Summary Metrics
# -------------------------------
def display_metrics(df_filtered):
    st.markdown("### Summary Metrics")
    pollutant_map = {
        'CO': 'CO AQI Value',
        'NO2': 'NO2 AQI Value',
        'PM2.5': 'PM2.5 AQI Value',
        'Ozone': 'Ozone AQI Value'
    }
    selected_summary = st.selectbox("Select Pollutant for Metric Summary", list(pollutant_map.keys()))
    col = pollutant_map[selected_summary]

    col1, col2, col3 = st.columns(3)
    col1.metric("Average AQI", round(df_filtered['AQI Value'].mean(), 2))
    col2.metric(f"Max {selected_summary} AQI", round(df_filtered[col].max(), 2) if col in df_filtered else "N/A")
    col3.metric(f"Min {selected_summary} AQI", round(df_filtered[col].min(), 2) if col in df_filtered else "N/A")

# -------------------------------
# Health Impact Estimator
# -------------------------------
def health_impact(df_filtered):
    st.markdown("### Air Quality Health Impact Estimator")
    if not df_filtered.empty:
        avg_aqi = df_filtered['AQI Value'].mean()
        if avg_aqi <= 50:
            impact = "🟢 Good — Little or no health risk."
        elif avg_aqi <= 100:
            impact = "🟡 Moderate — Sensitive individuals may experience minor symptoms."
        elif avg_aqi <= 150:
            impact = "🟠 Unhealthy for sensitive groups — People with respiratory issues should avoid exposure."
        elif avg_aqi <= 200:
            impact = "🔴 Unhealthy — Everyone may begin to experience health effects."
        elif avg_aqi <= 300:
            impact = "🟣 Very Unhealthy — Health warnings of emergency conditions."
        else:
            impact = "Hazardous — Serious health effects. Avoid all outdoor exposure."

        st.info(f"**Estimated Health Impact (avg AQI: {round(avg_aqi, 2)}):**\n\n{impact}")
    else:
        st.warning("No data available to estimate health impact.")

# -------------------------------
# Visualizations
# -------------------------------
def render_visuals(df_filtered, selected_countries):
    st.markdown("#### Top 10 Cities by Average AQI")
    chart_type = st.radio("Select Chart Type", ["Bar", "Line", "Area"], horizontal=True)
    top_cities = df_filtered.groupby('City')['AQI Value'].mean().sort_values(ascending=False).reset_index().head(10)

    if chart_type == "Bar":
        fig = px.bar(top_cities, x='City', y='AQI Value', color='AQI Value', color_continuous_scale='RdYlGn_r', template='plotly_white')
    elif chart_type == "Line":
        fig = px.line(top_cities, x='City', y='AQI Value', markers=True, template='plotly_white')
    else:
        fig = px.area(top_cities, x='City', y='AQI Value', template='plotly_white')

    fig.update_layout(xaxis_tickangle=-45, height=400, plot_bgcolor='#f9f9f9')
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### CO vs PM2.5 AQI Correlation")
    fig1 = px.scatter(df_filtered, x='CO AQI Value', y='PM2.5 AQI Value', color='AQI Category', hover_name='City', trendline='ols', template='plotly_white')
    fig1.update_traces(marker=dict(size=10, line=dict(width=1, color='black')))
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown("#### Ozone AQI Trend (Top 15 Cities)")
    ozone_df = df_filtered.groupby('City')['Ozone AQI Value'].mean().sort_values(ascending=False).reset_index().head(15)
    fig2 = px.line(ozone_df, x='City', y='Ozone AQI Value', markers=True, template='plotly_white')
    fig2.update_layout(xaxis_tickangle=-45, height=400, plot_bgcolor='#f9f9f9')
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### AQI Category Distribution")
    pie_df = df_filtered['AQI Category'].value_counts().reset_index()
    pie_df.columns = ['AQI Category', 'Count']
    fig3 = px.pie(pie_df, names='AQI Category', values='Count', hole=0.3, color_discrete_sequence=['green', 'orange', 'red'])
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("#### Interactive AQI Map")
    map_df = df_filtered.dropna(subset=['lat', 'lng'])
    if not map_df.empty:
        fig4 = px.scatter_geo(
            map_df, lat='lat', lon='lng', color='AQI Category', size='AQI Value',
            hover_name='City', projection='natural earth', template='plotly_white'
        )
        fig4.update_geos(
            showland=True, landcolor="lightgray", showcoastlines=True,
            showcountries=True, countrycolor="black", showframe=False, fitbounds="locations"
        )
        fig4.update_layout(margin=dict(l=0, r=0, t=50, b=0), height=600)
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.warning("No coordinates available to display map.")

# -------------------------------
# Advanced Features
# -------------------------------
def advanced_features(df_filtered, merged_df, selected_countries):
    st.markdown("### Advanced Feature: Conditional Content")
    with st.expander("Show PM2.5 Distribution Boxplot"):
        fig, ax = plt.subplots(figsize=(3.2, 0.9))
        sns.boxplot(data=df_filtered, x='PM2.5 AQI Value', ax=ax, color='skyblue')
        ax.set_title("PM2.5 AQI", fontsize=8, pad=4)
        ax.tick_params(labelsize=6)
        st.pyplot(fig)

    st.markdown("### Advanced Feature: Dynamic Configuration")
    c1, c2, c3 = st.columns(3)
    low = c1.slider("Low AQI threshold", 0, 100, 50)
    med = c2.slider("Moderate AQI threshold", low + 1, 200, 100)
    high = c3.slider("High AQI threshold", med + 1, 500, 150)

    def custom_category(aqi):
        if aqi <= low:
            return 'Good'
        elif aqi <= med:
            return 'Moderate'
        elif aqi <= high:
            return 'Unhealthy'
        return 'Hazardous'

    df_filtered['Custom AQI Category'] = df_filtered['AQI Value'].apply(custom_category)
    st.dataframe(df_filtered['Custom AQI Category'].value_counts().reset_index().rename(columns={'index': 'AQI Category', 'Custom AQI Category': 'Count'}))

    st.markdown("### Advanced Feature: Cascading Filter")
    if selected_countries:
        city_list = merged_df[merged_df['Country'].isin(selected_countries)]['City'].dropna().unique()
        selected_city = st.selectbox("Select City", sorted(city_list))
        city_df = merged_df[merged_df['City'] == selected_city]
        pollutants = ['CO AQI Value', 'PM2.5 AQI Value', 'NO2 AQI Value', 'Ozone AQI Value']
        selected_pollutants = st.multiselect("Select Pollutants", pollutants, default=pollutants)
        display_cols = ['City', 'Country', 'AQI Category'] + selected_pollutants
        st.dataframe(city_df[display_cols])
    else:
        st.warning("Please select at least one country to enable city filter.")

# -------------------------------
# Filtered Table and Download
# -------------------------------
def download_section(df_filtered):
    st.markdown("### Final Filtered Data Table")
    st.dataframe(df_filtered, use_container_width=True)

    st.markdown("### Download Filtered Dataset")
    csv = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Custom Filtered Data", data=csv, file_name="final_filtered_air_pollution_data.csv", mime='text/csv')

# -------------------------------
# Main
# -------------------------------
def main():
    apply_custom_css()
    merged_df = load_data()
    df_filtered, selected_countries, selected_pollutant = connected_filters(merged_df)
    display_metrics(df_filtered)
    health_impact(df_filtered)
    render_visuals(df_filtered, selected_countries)
    advanced_features(df_filtered, merged_df, selected_countries)
    download_section(df_filtered)

if __name__ == "__main__":
    main()
