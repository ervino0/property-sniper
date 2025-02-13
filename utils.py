import pandas as pd
import numpy as np

def load_and_clean_data(file):
    """Load and clean CSV data."""
    try:
        df = pd.read_csv(file)
        # Clean address column by removing extra whitespace and standardizing format
        df['Address'] = df['Address'].str.strip()

        # Format Year Built as integer
        if 'Year Built' in df.columns:
            df['Year Built'] = df['Year Built'].fillna(0).astype(int)

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

        # Create HTML link with data attributes for filtering
        return f'<a href="{url}" target="_blank" data-mls="{row["MLS"]}">{row["MLS"]}</a>'
    except Exception:
        return row['MLS']  # Return just the MLS number if link creation fails

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
    df['MLS Link'] = df.apply(generate_zealty_link, axis=1)

    display_columns = [
        'MLS Link', 'Address', 'Property Type', 'Bedrooms', 'Bathrooms', 'House Size (sqft)', 
        'List Price', 'Days on Market', 'Year Built', 'Listing Cancel Date'
    ]

    display_df = df[display_columns].copy()

    # Format currency
    display_df['List Price'] = display_df['List Price'].apply(
        lambda x: f"${x:,.0f}" if pd.notnull(x) else ''
    )

    return display_df

def apply_filters(df, raw_df, filters):
    """Apply filters to the dataframe."""
    mask = pd.Series(True, index=df.index)

    if filters.get('min_price'):
        mask &= (raw_df['List Price'] >= filters['min_price'])
    if filters.get('max_price'):
        mask &= (raw_df['List Price'] <= filters['max_price'])
    if filters.get('min_beds'):
        mask &= (raw_df['Bedrooms'] >= filters['min_beds'])
    if filters.get('max_beds'):
        mask &= (raw_df['Bedrooms'] <= filters['max_beds'])
    if filters.get('min_baths'):
        mask &= (raw_df['Bathrooms'] >= filters['min_baths'])
    if filters.get('max_baths'):
        mask &= (raw_df['Bathrooms'] <= filters['max_baths'])
    if filters.get('min_dom'):
        mask &= (raw_df['Days on Market'] >= filters['min_dom'])
    if filters.get('max_dom'):
        mask &= (raw_df['Days on Market'] <= filters['max_dom'])

    return df[mask]

def export_to_csv(df):
    """Prepare dataframe for CSV export."""
    # Remove HTML formatting from MLS Link column for CSV export
    export_df = df.copy()
    if 'MLS Link' in export_df.columns:
        export_df['MLS'] = export_df['MLS Link'].str.extract(r'>([^<]+)</a>')
        export_df = export_df.drop('MLS Link', axis=1)
    return export_df.to_csv(index=False)