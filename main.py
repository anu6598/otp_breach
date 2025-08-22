import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="OTP Request Analysis",
    page_icon="📊",
    layout="wide"
)

# Load the data
@st.cache_data
def load_data():
    data = pd.read_csv('f9268b3b-96a9-4e62-bf7e-920a82f844fd.csv')
    data['event_date'] = pd.to_datetime(data['event_date'])
    data['month'] = data['event_date'].dt.month
    data['month_name'] = data['event_date'].dt.month_name()
    data['year'] = data['event_date'].dt.year
    return data

data = load_data()

# Sidebar filters
st.sidebar.header("Filters")
start_date = st.sidebar.date_input(
    "Start date",
    value=data['event_date'].min(),
    min_value=data['event_date'].min(),
    max_value=data['event_date'].max()
)

end_date = st.sidebar.date_input(
    "End date",
    value=data['event_date'].max(),
    min_value=data['event_date'].min(),
    max_value=data['event_date'].max()
)

# Convert to datetime for filtering
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

# Filter data based on date selection
filtered_data = data[(data['event_date'] >= start_date) & (data['event_date'] <= end_date)]

# Main app
st.title("📊 OTP Request Analysis Dashboard")
st.markdown("Analyze OTP request patterns and evaluate current threshold effectiveness")

# Display data preview
st.header("Data Preview")
st.dataframe(filtered_data.head(10))

# Key metrics
st.header("Key Metrics")
col1, col2, col3, col4 = st.columns(4)

total_users = filtered_data['user_count'].sum()
users_over_threshold = filtered_data[filtered_data['otp_count'] > 16]['user_count'].sum()
percent_over_threshold = (users_over_threshold / total_users) * 100
max_otp_count = filtered_data['otp_count'].max()

col1.metric("Total Users", f"{total_users:,}")
col2.metric("Users > 16 OTPs", f"{users_over_threshold:,}")
col3.metric("% Over Threshold", f"{percent_over_threshold:.2f}%")
col4.metric("Max OTPs Requested", max_otp_count)

# Monthly trends
st.header("Monthly OTP Request Trends")

# Get unique months in the filtered data
months_in_range = filtered_data['month_name'].unique()
months_ordered = ['April', 'May', 'June', 'July', 'August']
available_months = [month for month in months_ordered if month in months_in_range]

# Create tabs for each month
tabs = st.tabs(available_months)

for i, month in enumerate(available_months):
    with tabs[i]:
        month_data = filtered_data[filtered_data['month_name'] == month]
        monthly_otp = month_data.groupby('otp_count')['user_count'].sum().reset_index()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=monthly_otp['otp_count'], 
            y=monthly_otp['user_count'],
            mode='lines+markers',
            name=month,
            line=dict(width=3)
        ))
        
        # Add threshold line
        fig.add_shape(
            type="line",
            x0=16, y0=0, x1=16, y1=max(monthly_otp['user_count']),
            line=dict(color="red", width=2, dash="dash"),
        )
        
        # Add annotation for threshold
        fig.add_annotation(
            x=16, y=max(monthly_otp['user_count']) * 0.9,
            text="Current Threshold: 16 OTPs",
            showarrow=True,
            arrowhead=1,
            ax=-50,
            ay=-30,
            bgcolor="white"
        )
        
        fig.update_layout(
            title=f"OTP Request Trends - {month}",
            xaxis_title="OTP Count",
            yaxis_title="User Count (Log Scale)",
            yaxis_type="log",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Month summary
        month_total = month_data['user_count'].sum()
        month_over_threshold = month_data[month_data['otp_count'] > 16]['user_count'].sum()
        month_percent = (month_over_threshold / month_total) * 100
        
        st.metric(f"{month} - Users Over Threshold", 
                 f"{month_over_threshold:,} ({month_percent:.2f}%)")

# Additional analysis
st.header("Threshold Analysis")
st.markdown(f"""
Based on the data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}:

- **{percent_over_threshold:.2f}%** of users exceeded the current threshold of 16 OTPs
- The maximum number of OTPs requested by a single user was **{max_otp_count}**
- The current threshold appears to be **{"appropriate" if percent_over_threshold < 0.5 else "potentially too restrictive"}** for most users
""")

if percent_over_threshold < 0.5:
    st.success("✅ The current threshold of 16 OTPs appears sufficient for most use cases.")
else:
    st.warning("⚠️ Consider reviewing the threshold as a significant portion of users are exceeding it.")

# Data summary by OTP count
st.header("Data Summary by OTP Count")
otp_summary = filtered_data.groupby('otp_count')['user_count'].sum().reset_index()
otp_summary['percentage'] = (otp_summary['user_count'] / otp_summary['user_count'].sum()) * 100
st.dataframe(otp_summary)

# Download option
csv = filtered_data.to_csv(index=False)
st.download_button(
    label="Download filtered data as CSV",
    data=csv,
    file_name="filtered_otp_data.csv",
    mime="text/csv"
)
