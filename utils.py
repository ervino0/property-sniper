import pandas as pd
import numpy as np

def load_and_clean_data(file):
    """Load and clean CSV data."""
    try:
        df = pd.read_csv(file)
        # Clean address column by removing extra whitespace and standardizing format
        df['Address'] = df['Address'].str.strip()
        return df
    except Exception as e:
        raise Exception(f"Error loading CSV file: {str(e)}")

def find_expired_unlisted_properties(off_market_df, sold_df, for_sale_df):
    """
    Find properties that are expired and not present in sold or active listings
    """
    # Get unique addresses from each dataset
    sold_addresses = set(sold_df['Address'].str.lower())
    active_addresses = set(for_sale_df['Address'].str.lower())

    # Filter expired properties
    expired_properties = off_market_df[
        (~off_market_df['Address'].str.lower().isin(sold_addresses)) & 
        (~off_market_df['Address'].str.lower().isin(active_addresses))
    ]

    return expired_properties

def prepare_display_data(df):
    """Prepare data for display by selecting and formatting relevant columns."""
    display_columns = [
        'MLS', 'Address', 'Bedrooms', 'Bathrooms', 'House Size (sqft)', 
        'List Price', 'Days on Market', 'Year Built'
    ]

    display_df = df[display_columns].copy()

    # Format MLS number as Zealty link
    display_df['MLS'] = display_df['MLS'].apply(
        lambda x: f'<a href="https://www.zealty.ca/mls-{x}/" target="_blank">{x}</a>' if pd.notnull(x) else ''
    )

    # Format currency
    display_df['List Price'] = display_df['List Price'].apply(
        lambda x: f"${x:,.0f}" if pd.notnull(x) else ''
    )

    return display_df

def export_to_csv(df):
    """Prepare dataframe for CSV export."""
    # Remove HTML formatting from MLS links for CSV export
    export_df = df.copy()
    export_df['MLS'] = export_df['MLS'].str.extract(r'>(\w+)<') 
    return export_df.to_csv(index=False)