import streamlit as st
import pandas as pd
import numpy as np
from io import StringIO
import base64

# Initialize session state variables for KPI calculation
if 'kpi_calculated' not in st.session_state:
    st.session_state.kpi_calculated = False
if 'kpi_df' not in st.session_state:
    st.session_state.kpi_df = None
if 'filtered_results' not in st.session_state:
    st.session_state.filtered_results = None

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

# Function to determine top 2 KPI focuses for an AG
def determine_kpi_focuses(row):
    # Initialize an empty list to store KPIs
    kpis = []
    
    # Ensure all required fields are numeric
    dormant_days = float(row['Dormant days'])
    surplus_cost = float(row['Surplus cost'])
    lost_sales = float(row['Lost sales'])
    availability = float(row['AVG availability (%)'])
    
    # Add KPIs based on specific conditions with proper numeric comparisons
    if dormant_days > 80:
        kpis.append("Dormant Inventory (Age)")
    if surplus_cost > 2 * lost_sales:
        kpis.append("Inventory Reduction")
    if availability < 75:
        kpis.append("Availability Improvement")
    
    # If we have fewer than 2 KPIs, add Sales Through
    if len(kpis) < 2:
        kpis.append("Sales Through")
    
    # If we still have fewer than 2 KPIs, add another one that's not already in the list
    if len(kpis) < 2:
        if "Inventory Reduction" not in kpis:
            kpis.append("Inventory Reduction")
        elif "Availability Improvement" not in kpis:
            kpis.append("Availability Improvement")
    
    # Ensure we return exactly 2 KPIs
    return kpis[:2]

# Legacy function for backward compatibility
def determine_kpi_focus(row):
    return determine_kpi_focuses(row)[0]
        
# Function to get rationale for KPI focus
def get_kpi_rationale(kpi):
    rationales = {
        "Dormant Inventory (Age)": "Indicates stagnant stock nearing obsolescence",
        "Inventory Reduction": "Surplus is the dominant problem to solve",
        "Availability Improvement": "Chronic stockouts risk lost sales and customer experience",
        "Sales Through": "Healthy balance → optimize sell-through further"
    }
    return rationales.get(kpi, "")

# Function to clean numeric columns
def clean_numeric_values(df):
    # Ensure all common numeric columns are properly converted to numeric types
    numeric_columns = [
        'SUM sales', 'Surplus cost', 'Lost sales', 'SKU Qty', 'Product Qty', 
        'AVG availability (%)', 'Dormant days', 'Total sales (£)', 'Total sales (units)', 
        'Global STR (%)', 'Global Discount STR (%)', 'Global Full price STR (%)', 
        'Local STR (%)', 'Local Discount STR (%)', 'Local Full Price STR (%)'
    ]
    
    for col in numeric_columns:
        if col in df.columns:
            # First convert any non-numeric characters or special characters
            df[col] = df[col].astype(str)  # Ensure it's a string first
            df[col] = df[col].replace({',': ''}, regex=True)  # Remove commas
            df[col] = df[col].replace({'—': '0', '-': '0', 'N/A': '0', 'n/a': '0'}, regex=True)  # Replace dash with zero
            
            # Then convert to numeric, handling any errors
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df

# Main app header
st.markdown('<h1 class="main-header">AG Selection Tool</h1>', unsafe_allow_html=True)
st.markdown('<p class="subheader">Find optimal assortment groups for your pilot program</p>', 
            unsafe_allow_html=True)

# File uploader sections
st.markdown("### Upload Data Files")
col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader("Upload Performance Data CSV", type=["csv"], key="perf_data")

with col2:
    season_file = st.file_uploader("Upload Seasonal Analysis CSV (required)", type=["csv"], key="season_data")

if uploaded_file is not None:
    # Read the CSV file
    try:
        df = pd.read_csv(uploaded_file)
        # Clean the data
        df = clean_numeric_values(df)
        
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
            value=(50, 95),
            help="Select AGs with average availability in this range"
        )
        
        # SKU and Product thresholds
        col1, col2 = st.columns(2)
        with col1:
            min_skus = st.number_input(
                "Minimum SKUs", 
                min_value=0, 
                value=10,
                help="Minimum number of SKUs required"
            )
        
        with col2:
            min_products = st.number_input(
                "Minimum Products", 
                min_value=0, 
                value=10,
                help="Minimum number of products required"
            )
        
        # Dynamics criteria
        col1, col2 = st.columns(2)
        with col1:
            min_surplus = st.number_input(
                "Minimum Surplus Cost", 
                min_value=0, 
                value=100,
                help="Minimum surplus cost value required"
            )
        
        with col2:
            min_lost_sales = st.number_input(
                "Minimum Lost Sales", 
                min_value=0, 
                value=100,
                help="Minimum lost sales value required"
            )
            
        # New parameters for dormant and salethrough
        col1, col2 = st.columns(2)
        with col1:
            min_age = st.number_input(
                "Minimum Average Age (days)", 
                min_value=0, 
                value=30,
                help="Minimum average age in days (dormant inventory filter)"
            )
        
        with col2:
            max_salethrough = st.number_input(
                "Maximum Salethrough Rate (%)", 
                min_value=0, 
                max_value=100,
                value=80,
                help="Maximum salethrough percentage required"
            )
        
        # Run Analysis button
        analyze_button = st.button("Run Analysis", type="primary", key="analyze_button")
        
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
                
                # Apply dynamics criteria for surplus and lost sales
                filtered_df = filtered_df[filtered_df['Surplus cost'] > min_surplus]
                filtered_df = filtered_df[filtered_df['Lost sales'] > min_lost_sales]
                
                # Apply new filters for dormant (age) - now MINIMUM age
                filtered_df = filtered_df[filtered_df['Dormant days'] >= min_age]
                
                # For salethrough, both files are required
                if season_file is None:
                    st.error("Seasonal analysis data (second CSV) is required. Please upload both CSV files.")
                    st.stop()  # Using st.stop() instead of return
                
                seasonal_data_valid = True
                
                try:
                    season_df = pd.read_csv(season_file)
                    season_df = clean_numeric_values(season_df)
                    
                    # Merge the dataframes on AG to get the salethrough data
                    # We're using Global STR as the salethrough metric
                    if 'Global STR (%)' in season_df.columns:
                        merged_df = pd.merge(filtered_df, 
                                          season_df[['AG', 'Global STR (%)']], 
                                          on='AG', how='inner')  # Using inner join to require matches
                        
                        # Apply the salethrough filter - now MAXIMUM salethrough
                        if 'Global STR (%)' in merged_df.columns:
                            filtered_df = merged_df[merged_df['Global STR (%)'] <= max_salethrough]
                        else:
                            st.error("Required column 'Global STR (%)' not found in seasonal data.")
                            seasonal_data_valid = False
                    else:
                        st.error("Required column 'Global STR (%)' not found in seasonal data.")
                        seasonal_data_valid = False
                except Exception as e:
                    st.error(f"Error processing seasonal data: {e}")
                    seasonal_data_valid = False
                    
                if not seasonal_data_valid:
                    st.stop()  # Stop execution if seasonal data is invalid
                
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
                    
                    # Calculate KPIs for each AG first
                    kpi_df = filtered_df.copy()
                    
                    # Get two KPIs for each AG
                    kpi_list = []
                    kpi_by_ag = {}
                    
                    for idx, row in kpi_df.iterrows():
                        ag_name = row['AG']
                        kpis = determine_kpi_focuses(row)
                        
                        # Store the KPIs joined by comma for this AG
                        kpi_by_ag[ag_name] = ', '.join(kpis)
                        
                        for kpi in kpis:
                            kpi_list.append({
                                'AG': ag_name,
                                'KPI Focus': kpi,
                                'Rationale': get_kpi_rationale(kpi)
                            })
                    
                    # Convert to dataframe for KPI analysis
                    kpi_results = pd.DataFrame(kpi_list)
                    
                    # Store results in session state
                    st.session_state.kpi_df = kpi_results
                    
                    # Add KPI columns to the filtered results dataframe
                    filtered_df['KPI Recommendations'] = filtered_df['AG'].map(kpi_by_ag)
                    
                    # Store the updated filtered dataframe in session state
                    st.session_state.filtered_results = filtered_df.copy()
                    
                    # Complete results in a table with KPIs integrated
                    st.markdown("### Complete Results with KPI Recommendations")
                    
                    # Reorder columns to put KPI Recommendations right after AG
                    cols = list(filtered_df.columns)
                    cols.remove('AG')
                    cols.remove('KPI Recommendations')
                    ordered_cols = ['AG', 'KPI Recommendations'] + cols
                    
                    # Show the reordered dataframe
                    st.dataframe(
                        filtered_df[ordered_cols].style.format({
                            'SUM sales': '${:,.2f}',
                            'AVG availability (%)': '{:.2f}%',
                            'Surplus cost': '${:,.2f}',
                            'Lost sales': '{:,.2f}'
                        }),
                        height=300
                    )
                    
                    # Download button
                    st.markdown(get_csv_download_link(filtered_df), unsafe_allow_html=True)
                    
                    # Add KPI analysis section
                    st.markdown("### KPI Analysis")
                    
                    # Calculate KPI counts for the bar chart
                    kpi_counts = kpi_results['KPI Focus'].value_counts().reset_index()
                    kpi_counts.columns = ['KPI', 'Count']
                    
                    # Display bar chart of KPI distribution
                    st.markdown("#### KPI Distribution Across All AGs")
                    
                    # Setup the chart
                    st.bar_chart(
                        kpi_counts, 
                        x='KPI',
                        y='Count',
                        color="#1F6C6D"
                    )
                    
                    # Calculate percentages for the total pool
                    total_kpis = len(kpi_list)
                    
                    st.markdown("#### KPI Impact Analysis")
                    st.markdown("""
                    <div class="warning-card">
                        <h4>KPI Distribution Summary:</h4>
                    """, unsafe_allow_html=True)
                    
                    for idx, row in kpi_counts.iterrows():
                        kpi = row['KPI']
                        count = row['Count']
                        percentage = round((count / total_kpis) * 100, 1)
                        rationale = get_kpi_rationale(kpi)
                        st.markdown(f"""
                        <p><strong>{kpi}</strong> ({percentage}% of KPIs) - {rationale}</p>
                        """, unsafe_allow_html=True)
                        
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Download button
                    st.markdown("#### Download KPI Analysis")
                    st.markdown(get_csv_download_link(kpi_results, "kpi_recommendations.csv"), 
                                unsafe_allow_html=True)
                    
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
            <li>Upload <strong>both</strong> your AG performance CSV file and seasonal analysis CSV file (both are required)</li>
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
        ### Performance Data CSV
        Your main performance data CSV file should have these columns:
        - `AG`: Assortment Group name/identifier
        - `SUM sales`: Total sales amount
        - `SKU Qty`: Number of SKUs in the assortment group
        - `Product Qty`: Number of distinct products
        - `AVG availability (%)`: Average product availability percentage
        - `Dormant days`: Average age of dormant inventory in days
        - `Surplus cost`: Cost of surplus inventory
        - `Lost sales`: Value of lost sales opportunities
        
        ### Seasonal Analysis CSV (Required)
        The seasonal analysis CSV is required and should have these columns:
        - `AG`: Assortment Group name/identifier (must match the AG values in the performance data)
        - `Global STR (%)`: Global sales-through rate percentage (required)
        - `Local STR (%)`: Local sales-through rate percentage
        - Additional metrics like discount rates, unit sales, etc.
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #1A314B;">
    <p>AG Selection Tool | Developed with Streamlit</p>
</div>
""", unsafe_allow_html=True)