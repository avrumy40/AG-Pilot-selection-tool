# AG Selection Tool

A Streamlit-based tool that helps users identify optimal assortment groups (AGs) for piloting based on customizable performance criteria.

## Features

- **Data Upload**: Upload your AG performance data in CSV format
- **Flexible Filtering**: Customizable filtering options for performance metrics
- **Visual Results**: Clear, visually appealing display of recommended AGs
- **Downloadable Results**: Export filtered AGs as CSV for further analysis

## Filtering Criteria

The tool applies several best practices for AG selection:

1. **Mid-performing AGs**: Filters out top 20% and bottom 30% by sales
2. **Balanced Availability**: Targets AGs with 50%-90% availability
3. **Active Dynamics**: Requires both surplus and lost sales
4. **Sufficient Assortment Richness**: Minimum SKUs and products

## Required CSV Format

Your input file should include these columns:
- `AG`: Assortment Group name/identifier
- `SUM sales`: Total sales amount
- `SKU Qty`: Number of SKUs in the assortment group
- `Product Qty`: Number of distinct products
- `AVG availability (%)`: Average product availability percentage
- `AVG age days`: Average age of products in days
- `Surplus cost`: Cost of surplus inventory
- `Lost sales`: Value of lost sales opportunities

## Deployment

This app is configured for deployment on Streamlit cloud or any Streamlit-compatible hosting service.

## Technologies

- **Streamlit**: For the web application framework
- **Pandas**: For data manipulation
- **Numpy**: For numerical operations
- **Plotly**: For data visualization (if used)