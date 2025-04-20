import streamlit as st
import pymongo
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import numpy as np

# Set Streamlit Page Config with improved styling
st.set_page_config(
    page_title="Student Performance Analysis", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to enhance the dashboard appearance
st.markdown("""
    <style>
    .main {
        padding: 1rem 2rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .dashboard-header {
        margin-bottom: 1.5rem;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #4e54c8, #8f94fb);
        color: white;
        border-radius: 10px;
    }
    .metric-container {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    </style>
    <div class="dashboard-header">
        <h1>Student Performance Analytics Dashboard</h1>
    </div>
""", unsafe_allow_html=True)

# Load environment variables
load_dotenv()

# MongoDB Connection
client = MongoClient(os.environ.get('MONGO_DB_URI'))

# Retrieve student ID and quiz ID from session
student_id = st.session_state.get("student_id")
quiz_id = st.session_state.get("quiz_id")  # Quiz student attempted

if not student_id or not quiz_id:
    st.error("❌ Error: Missing student ID or quiz ID.")
    st.stop()

# Extract Subject Name from quiz_id (e.g., "history" from "history101")
subject_name = "".join(filter(str.isalpha, quiz_id)).lower()

# Connect to the Correct Database
db = client[subject_name]

# Ensure "test_scores" collection exists
if "test_scores" not in db.list_collection_names():
    st.error(f"❌ Collection 'test_scores' not found in database '{subject_name}'.")
    st.stop()

collection = db["test_scores"]

# Fetch Student's Test Data
student_data = list(collection.find({"student_id": student_id}))

if not student_data:
    st.warning(f"⚠️ No test data found for Student ID: {student_id}")
    st.stop()

# Convert to DataFrame
df = pd.DataFrame(student_data)
df.columns = df.columns.str.strip().str.lower()  # Ensure consistency

df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.sort_values("timestamp")

# Calculate additional metrics
df["accuracy"] = (df["score"] / df["total"]) * 100
df["performance_category"] = pd.cut(
    df["accuracy"],
    bins=[0, 60, 75, 90, 100],
    labels=["Needs Improvement", "Satisfactory", "Good", "Excellent"]
)

# Create sidebar for interactive filtering
with st.sidebar:
    st.image("https://via.placeholder.com/150?text=Student", width=150)
    st.subheader(f"Student ID: {student_id}")
    st.subheader(f"Subject: {subject_name.capitalize()}")
    
    st.divider()
    
    # Date range filter
    st.subheader("Filter Data")
    min_date = df["timestamp"].min().date()
    max_date = df["timestamp"].max().date()
    
    date_range = st.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = df[(df["timestamp"].dt.date >= start_date) & 
                         (df["timestamp"].dt.date <= end_date)]
    else:
        filtered_df = df
    
    # Quiz filter
    selected_quizzes = st.multiselect(
        "Select Quizzes",
        options=df["quiz_id"].unique(),
        default=df["quiz_id"].unique()
    )
    
    if selected_quizzes:
        filtered_df = filtered_df[filtered_df["quiz_id"].isin(selected_quizzes)]
        
    st.divider()
    
    # Download option
    if st.download_button(
        "Download Performance Data",
        filtered_df.to_csv(index=False).encode('utf-8'),
        f"student_{student_id}_performance.csv",
        "text/csv"
    ):
        st.success("Data downloaded successfully!")

# Main dashboard area
# Key Performance Indicators
st.subheader("📊 Key Performance Metrics")

# KPI metrics in a row
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

latest_score = df.iloc[-1]
avg_accuracy = filtered_df["accuracy"].mean()
total_quizzes = filtered_df["quiz_id"].nunique()
performance_trend = "↗️ Improving" if filtered_df["accuracy"].iloc[-1] > filtered_df["accuracy"].iloc[0] else "↘️ Declining"

with kpi1:
    st.metric(
        "Latest Score",
        f"{latest_score['score']} / {latest_score['total']}",
        f"{latest_score['accuracy']:.1f}%"
    )

with kpi2:
    st.metric(
        "Average Accuracy",
        f"{avg_accuracy:.1f}%"
    )

with kpi3:
    st.metric(
        "Total Quizzes Taken",
        f"{total_quizzes}"
    )
    
with kpi4:
    st.metric(
        "Performance Trend",
        performance_trend
    )

# Create two columns for charts
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Score Progression")
    
    # Interactive line chart with range slider
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=filtered_df["timestamp"],
        y=filtered_df["score"],
        mode='lines+markers',
        name='Score',
        line=dict(color='#4e54c8', width=3),
        marker=dict(size=8)
    ))
    
    fig.add_trace(go.Scatter(
        x=filtered_df["timestamp"],
        y=filtered_df["total"],
        mode='lines',
        name='Total Possible',
        line=dict(color='#8f94fb', width=2, dash='dash')
    ))
    
    fig.update_layout(
        title='Score Progression Over Time',
        height=400,
        hovermode='x unified',
        legend=dict(orientation='h', y=1.1),
        xaxis=dict(
            rangeslider=dict(visible=True),
            type='date'
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📊 Performance Distribution")
    
    # Performance category distribution
    category_counts = filtered_df["performance_category"].value_counts().reset_index()
    category_counts.columns = ["Category", "Count"]
    
    # Custom color scale based on categories
    color_scale = {
        "Needs Improvement": "#ff6b6b", 
        "Satisfactory": "#ffd166", 
        "Good": "#4ecdc4", 
        "Excellent": "#06d6a0"
    }
    
    colors = [color_scale.get(cat, "#000000") for cat in category_counts["Category"]]
    
    fig = go.Figure(data=[go.Pie(
        labels=category_counts["Category"],
        values=category_counts["Count"],
        hole=.3,
        marker=dict(colors=colors),
        textinfo='label+percent',
        hoverinfo='label+value',
        textfont=dict(size=14)
    )])
    
    fig.update_layout(
        title="Performance Categories Distribution",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Performance heatmap by quiz
st.subheader("🔥 Performance Heatmap by Quiz")

# Create a pivot table for the heatmap
if len(filtered_df) > 1:
    # Create quiz performance heatmap
    quiz_pivot = filtered_df.pivot_table(
        index=filtered_df["timestamp"].dt.strftime('%Y-%m-%d'),
        columns="quiz_id",
        values="accuracy",
        aggfunc="mean"
    ).fillna(0)
    
    fig = px.imshow(
        quiz_pivot,
        labels=dict(x="Quiz ID", y="Date", color="Accuracy %"),
        x=quiz_pivot.columns,
        y=quiz_pivot.index,
        color_continuous_scale="Blues",
        aspect="auto",
        text_auto=True
    )
    
    fig.update_layout(
        height=400,
        xaxis=dict(side="top")
    )
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Not enough data to generate performance heatmap.")

# Interactive quiz comparison
st.subheader("🔄 Quiz Performance Comparison")

# Bar chart with interactive elements
fig = px.bar(
    filtered_df,
    x="quiz_id",
    y="accuracy",
    color="accuracy",
    color_continuous_scale=["red", "yellow", "green"],
    range_color=[0, 100],
    labels={"accuracy": "Accuracy (%)", "quiz_id": "Quiz ID"},
    text=filtered_df["score"].astype(str) + "/" + filtered_df["total"].astype(str),
    hover_data=["timestamp", "score", "total"]
)

fig.update_layout(
    height=400,
    xaxis_title="Quiz ID",
    yaxis_title="Accuracy (%)",
    yaxis=dict(range=[0, 100]),
    hovermode="closest"
)

fig.add_shape(
    type="line",
    x0=-0.5,
    y0=avg_accuracy,
    x1=len(filtered_df["quiz_id"].unique()) - 0.5,
    y1=avg_accuracy,
    line=dict(
        color="black",
        width=2,
        dash="dash",
    ),
    name="Average"
)

fig.add_annotation(
    x=len(filtered_df["quiz_id"].unique()) - 1,
    y=avg_accuracy,
    text=f"Average: {avg_accuracy:.1f}%",
    showarrow=False,
    yshift=10
)

st.plotly_chart(fig, use_container_width=True)

# Detailed data view with tabs
st.subheader("📋 Detailed Performance Data")

tab1, tab2 = st.tabs(["📄 Data Table", "📊 Performance Metrics"])

with tab1:
    # Interactive data table with formatting
    st.dataframe(
        filtered_df[["quiz_id", "score", "total", "accuracy", "timestamp", "performance_category"]],
        column_config={
            "accuracy": st.column_config.ProgressColumn(
                "Accuracy (%)",
                format="%.1f%%",
                min_value=0,
                max_value=100
            ),
            "timestamp": st.column_config.DatetimeColumn(
                "Date & Time",
                format="MMM DD, YYYY - HH:mm"
            ),
            "performance_category": st.column_config.TextColumn(
                "Performance Level"
            )
        },
        use_container_width=True,
        hide_index=True
    )

with tab2:
    metric_col1, metric_col2 = st.columns(2)
    
    with metric_col1:
        # Time-based performance analysis
        time_analysis = filtered_df.set_index("timestamp")
        time_analysis = time_analysis.resample('D')['accuracy'].mean().reset_index()
        time_analysis = time_analysis.dropna()
        
        if not time_analysis.empty:
            fig = px.line(
                time_analysis, 
                x="timestamp", 
                y="accuracy",
                markers=True,
                labels={"timestamp": "Date", "accuracy": "Average Accuracy (%)"},
                title="Daily Average Performance"
            )
            
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough time-series data for daily analysis.")
    
    with metric_col2:
        # Progress towards mastery visualization
        mastery_threshold = 90  # 90% accuracy considered mastery
        
        latest_accuracies = filtered_df.groupby("quiz_id")["accuracy"].last().reset_index()
        
        fig = go.Figure()
        
        for i, row in latest_accuracies.iterrows():
            fig.add_trace(go.Indicator(
                mode="gauge+number",
                value=row["accuracy"],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': f"Quiz: {row['quiz_id']}"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 60], 'color': "#ff6b6b"},
                        {'range': [60, 75], 'color': "#ffd166"},
                        {'range': [75, 90], 'color': "#4ecdc4"},
                        {'range': [90, 100], 'color': "#06d6a0"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': mastery_threshold
                    }
                }
            ))
        
        fig.update_layout(
            grid={'rows': 1, 'columns': min(3, len(latest_accuracies))},
            height=300,
            title_text="Progress Towards Mastery (90%)"
        )
        
        st.plotly_chart(fig, use_container_width=True)

# Recommendations section based on performance
st.subheader("💡 Performance Insights & Recommendations")

# Simple recommendation logic
recent_performance = filtered_df.sort_values("timestamp").tail(3)["accuracy"].mean()
overall_performance = filtered_df["accuracy"].mean()

insight_col1, insight_col2 = st.columns(2)

with insight_col1:
    st.markdown("""
    <div class="metric-container">
        <h4>Performance Trend Analysis</h4>
    """, unsafe_allow_html=True)
    
    if recent_performance > overall_performance + 5:
        st.success("📈 Your recent performance shows significant improvement! Keep up the good work.")
    elif recent_performance < overall_performance - 5:
        st.warning("📉 Your recent performance has declined. Consider reviewing earlier materials.")
    else:
        st.info("📊 Your performance has been consistent. Focus on specific areas to improve.")
    
    # Find strongest and weakest quizzes
    if len(filtered_df) > 1:
        quiz_avg = filtered_df.groupby("quiz_id")["accuracy"].mean().reset_index()
        best_quiz = quiz_avg.loc[quiz_avg["accuracy"].idxmax()]
        worst_quiz = quiz_avg.loc[quiz_avg["accuracy"].idxmin()]
        
        st.markdown(f"**Strongest Performance**: Quiz {best_quiz['quiz_id']} ({best_quiz['accuracy']:.1f}%)")
        st.markdown(f"**Needs Improvement**: Quiz {worst_quiz['quiz_id']} ({worst_quiz['accuracy']:.1f}%)")
    
    st.markdown("</div>", unsafe_allow_html=True)

with insight_col2:
    st.markdown("""
    <div class="metric-container">
        <h4>Study Recommendations</h4>
    """, unsafe_allow_html=True)
    
    # Simple recommendation system
    below_threshold = filtered_df[filtered_df["accuracy"] < 75]
    
    if not below_threshold.empty:
        st.markdown("**Focus Areas for Improvement:**")
        for quiz in below_threshold["quiz_id"].unique():
            accuracy = below_threshold[below_threshold["quiz_id"] == quiz]["accuracy"].mean()
            st.markdown(f"- Review material for Quiz {quiz} ({accuracy:.1f}%)")
    else:
        st.success("Great job! All quiz scores are above the satisfactory threshold.")
    
    if recent_performance > 90:
        st.markdown("**Next Steps**: Consider taking more advanced quizzes to challenge yourself.")
    
    st.markdown("</div>", unsafe_allow_html=True)

# Footer with attribution
st.markdown("""
---
<div style='text-align: center; color: #666;'>
    
    <p>Last updated: {}</p>
</div>
""".format(datetime.now().strftime("%Y-%m-%d")), unsafe_allow_html=True)