import streamlit as st
import pandas as pd
import numpy as np
from io import StringIO
import base64

# Set page config
st.set_page_config(
    page_title="AG Selection Tool",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Custom CSS
def add_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Poppins', sans-serif;
        font-weight: 700;
    }
    
    .main-header {
        color: #1A314B;
        font-weight: 700;
    }
    
    .subheader {
        color: #1F6C6D;
        font-weight: 400;
    }
    
    .highlight {
        color: #FD604A;
    }
    
    .stButton button {
        background-color: #1F6C6D;
        color: white;
        font-family: 'Poppins', sans-serif;
    }
    
    .stButton button:hover {
        background-color: #184E4F;
    }
    
    .st-eb {
        background-color: #1F6C6D;
    }
    
    .stDownloadButton button {
        background-color: #1A314B;
        color: white;
    }
    
    .success-card {
        background-color: #f0f7f7;
        padding: 20px;
        border-radius: 5px;
        border-left: 5px solid #1F6C6D;
        margin-bottom: 15px;
    }
    
    .warning-card {
        background-color: #fff7f0;
        padding: 20px;
        border-radius: 5px;
        border-left: 5px solid #FD604A;
    }
    
    .metric-card {
        background-color: white;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #1F6C6D;
    }
    
    .metric-label {
        font-size: 14px;
        color: #1A314B;
    }
    </style>
    """, unsafe_allow_html=True)

add_custom_css()

# Function to download dataframe as CSV
def get_csv_download_link(df, filename="filtered_results.csv"):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}" class="download-button">Download CSV</a>'
    return href

# Function to clean numeric columns
def clean_numeric_values(df):
    for col in ['SUM sales', 'Surplus cost', 'Lost sales']:
        if col in df.columns:
            # Remove commas and convert to float
            df[col] = df[col].replace({',': ''}, regex=True)
            df[col] = df[col].replace({'—': '0'}, regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

# Main app header
st.markdown('<h1 class="main-header">AG Selection Tool</h1>', unsafe_allow_html=True)
st.markdown('<p class="subheader">Find optimal assortment groups for your pilot program</p>', 
            unsafe_allow_html=True)

# File uploader section
uploaded_file = st.file_uploader("Upload AG Performance CSV", type=["csv"])

if uploaded_file is not None:
    # Read the CSV file
    try:
        df = pd.read_csv(uploaded_file)
        # Clean the data
        df = clean_numeric_values(df)
        
        st.success("File uploaded successfully!")
        
        # Parameters section in columns
        st.markdown("### Configure Parameters")
        
        # Sales filtering
        col1, col2 = st.columns(2)
        with col1:
            top_sales_percentile = st.slider(
                "Exclude Top Sales (%)", 
                min_value=0, 
                max_value=50, 
                value=20,
                help="Filter out top performers by total sales"
            )
        
        with col2:
            bottom_sales_percentile = st.slider(
                "Exclude Bottom Sales (%)", 
                min_value=0, 
                max_value=50, 
                value=30,
                help="Filter out bottom performers by total sales"
            )
        
        # Availability filtering
        min_availability, max_availability = st.slider(
            "Target Availability Range (%)", 
            min_value=0, 
            max_value=100, 
            value=(50, 90),
            help="Select AGs with average availability in this range"
        )
        
        # SKU and Product thresholds
        col1, col2 = st.columns(2)
        with col1:
            min_skus = st.number_input(
                "Minimum SKUs", 
                min_value=0, 
                value=150,
                help="Minimum number of SKUs required"
            )
        
        with col2:
            min_products = st.number_input(
                "Minimum Products", 
                min_value=0, 
                value=40,
                help="Minimum number of products required"
            )
        
        # Dynamics criteria
        col1, col2 = st.columns(2)
        with col1:
            min_surplus = st.number_input(
                "Minimum Surplus Cost", 
                min_value=0, 
                value=1000,
                help="Minimum surplus cost value required"
            )
        
        with col2:
            min_lost_sales = st.number_input(
                "Minimum Lost Sales", 
                min_value=0, 
                value=1000,
                help="Minimum lost sales value required"
            )
        
        # Run Analysis button
        analyze_button = st.button("Run Analysis", type="primary")
        
        # Main content area
        if analyze_button:
            # Apply filters
            # Calculate percentile thresholds for sales
            if len(df) > 0:
                top_threshold = np.percentile(df['SUM sales'], 100 - top_sales_percentile)
                bottom_threshold = np.percentile(df['SUM sales'], bottom_sales_percentile)
                
                # Initial filtering based on sales percentiles
                filtered_df = df[(df['SUM sales'] < top_threshold) & (df['SUM sales'] > bottom_threshold)]
                
                # Apply availability filter
                filtered_df = filtered_df[(filtered_df['AVG availability (%)'] >= min_availability) & 
                                        (filtered_df['AVG availability (%)'] <= max_availability)]
                
                # Apply assortment richness filter
                filtered_df = filtered_df[(filtered_df['SKU Qty'] >= min_skus) & 
                                        (filtered_df['Product Qty'] >= min_products)]
                
                # Apply dynamics criteria
                filtered_df = filtered_df[filtered_df['Surplus cost'] > min_surplus]
                filtered_df = filtered_df[filtered_df['Lost sales'] > min_lost_sales]
                
                # Display summary results
                st.markdown("### Analysis Results")
                
                # Show the number of AGs before and after filtering
                total_ags = len(df)
                filtered_ags = len(filtered_df)
                
                st.markdown(f"""
                <div class="success-card">
                    <h3>Summary</h3>
                    <p>Total AGs: {total_ags}</p>
                    <p>AGs meeting all criteria: {filtered_ags}</p>
                    <p>Percentage selected: {round((filtered_ags/total_ags)*100 if total_ags > 0 else 0, 2)}%</p>
                </div>
                """, unsafe_allow_html=True)
                
                if filtered_ags == 0:
                    st.warning("No AGs match the current criteria. Try adjusting your parameters.")
                
                # Final recommendations section
                if not filtered_df.empty:
                    st.markdown("### Recommended AGs for Pilot")
                    
                    # Sort by sales to get top recommendations
                    top_recommendations = filtered_df.sort_values('SUM sales', ascending=False).head(5)
                    
                    for i, (idx, row) in enumerate(top_recommendations.iterrows(), 1):
                        st.markdown(f"""
                        <div class="success-card">
                            <h4>{i}. {row['AG']}</h4>
                            <p><strong>Sales:</strong> ${row['SUM sales']:,.2f} | 
                            <strong>Availability:</strong> {row['AVG availability (%)']:.2f}%</p>
                            <p><strong>SKUs:</strong> {row['SKU Qty']} | 
                            <strong>Products:</strong> {row['Product Qty']}</p>
                            <p><strong>Dynamics:</strong> Surplus Cost: ${row['Surplus cost']:,.2f} | 
                            Lost Sales: ${row['Lost sales']:,.2f}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Complete results in a table
                    st.markdown("### Complete Results")
                    st.dataframe(
                        filtered_df.style.format({
                            'SUM sales': '${:,.2f}',
                            'AVG availability (%)': '{:.2f}%',
                            'Surplus cost': '${:,.2f}',
                            'Lost sales': '{:,.2f}'
                        }),
                        height=300
                    )
                    
                    # Download button
                    st.markdown(get_csv_download_link(filtered_df), unsafe_allow_html=True)
                    
                else:
                    st.warning("No recommendations available with current parameters. Please adjust your filters.")
            else:
                st.error("No data available for analysis.")
        else:
            st.info("Configure your parameters and click 'Run Analysis' to see results.")
    except Exception as e:
        st.error(f"Error processing file: {e}")
        df = None
else:
    # Display a welcome page if no file is uploaded
    st.markdown("""
    <div class="warning-card">
        <h2>Welcome to the AG Selection Tool!</h2>
        <p>This tool helps you identify optimal assortment groups (AGs) for piloting based on performance criteria.</p>
        <h3>To get started:</h3>
        <ol>
            <li>Upload your AG performance CSV file</li>
            <li>Configure the filtering parameters to match your business needs</li>
            <li>Click the "Run Analysis" button</li>
            <li>Review the recommended AGs and download results if needed</li>
        </ol>
        <p>The tool automatically applies best practices for AG selection including:</p>
        <ul>
            <li>Focusing on mid-performing AGs (filtering out extremes)</li>
            <li>Targeting balanced availability</li>
            <li>Ensuring active dynamics (both surplus and lost sales)</li>
            <li>Verifying sufficient assortment richness</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Show example of expected CSV format
    with st.expander("Expected CSV Format"):
        st.markdown("""
        Your CSV file should have these columns:
        - `AG`: Assortment Group name/identifier
        - `SUM sales`: Total sales amount
        - `SKU Qty`: Number of SKUs in the assortment group
        - `Product Qty`: Number of distinct products
        - `AVG availability (%)`: Average product availability percentage
        - `AVG age days`: Average age of products in days
        - `Surplus cost`: Cost of surplus inventory
        - `Lost sales`: Value of lost sales opportunities
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #1A314B;">
    <p>AG Selection Tool | Developed with Streamlit</p>
</div>
""", unsafe_allow_html=True)