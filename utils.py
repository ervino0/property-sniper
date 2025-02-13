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

def generate_zealty_link(row):
    """Generate Zealty.ca link from MLS and address."""
    try:
        # Extract components from address
        address_parts = row['Address'].split(' ')
        street_num = address_parts[0]
        # Find where city starts (assuming it's after "Vancouver" or similar)
        city_idx = next(i for i, part in enumerate(address_parts) if part in ['Vancouver', 'Surrey'])
        street_name = ' '.join(address_parts[1:city_idx])
        city = address_parts[city_idx]
        province = address_parts[city_idx + 1]

        # Format components
        street_name = street_name.replace(' ', '-').upper()

        # Create URL
        url = f"https://www.zealty.ca/mls-{row['MLS']}/{street_num}-{street_name}-{city}-{province}/"

        return {'display_value': row['MLS'], 'url': url}
    except Exception:
        return {'display_value': row['MLS'], 'url': ''}

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
    # Generate Zealty links for MLS numbers
    links = df.apply(generate_zealty_link, axis=1)
    df['MLS'] = links.apply(lambda x: x['display_value'])
    df['Zealty URL'] = links.apply(lambda x: x['url'])

    display_columns = [
        'MLS', 'Zealty URL', 'Address', 'Bedrooms', 'Bathrooms', 'House Size (sqft)', 
        'List Price', 'Days on Market', 'Year Built'
    ]

    display_df = df[display_columns].copy()

    # Format currency
    display_df['List Price'] = display_df['List Price'].apply(
        lambda x: f"${x:,.0f}" if pd.notnull(x) else ''
    )

    return display_df

def export_to_csv(df):
    """Prepare dataframe for CSV export."""
    export_df = df.copy()
    if 'Zealty URL' in export_df.columns:
        export_df = export_df.drop('Zealty URL', axis=1)
    return export_df.to_csv(index=False)