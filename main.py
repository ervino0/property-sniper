import streamlit as st
import pandas as pd
import base64
from utils import (
    load_and_clean_data,
    find_expired_unlisted_properties,
    prepare_display_data,
    export_to_csv
)

# Page configuration
st.set_page_config(
    page_title="Real Estate Listing Analysis",
    page_icon="🏠",
    layout="wide"
)

# Load custom CSS
with open('styles.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def main():
    st.title("Real Estate Listing Analysis")
    st.markdown("""
    <div style='background-color: #EDF2F7; padding: 1rem; border-radius: 4px; margin-bottom: 2rem;'>
        Upload your real estate listing files to identify expired properties that haven't been sold 
        and aren't currently on the market.
    </div>
    """, unsafe_allow_html=True)

    # File upload section
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("<div class='upload-area'>", unsafe_allow_html=True)
        off_market_file = st.file_uploader("Upload Off-Market Listings", type=['csv'])
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='upload-area'>", unsafe_allow_html=True)
        sold_file = st.file_uploader("Upload Sold Listings", type=['csv'])
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<div class='upload-area'>", unsafe_allow_html=True)
        for_sale_file = st.file_uploader("Upload For-Sale Listings", type=['csv'])
        st.markdown("</div>", unsafe_allow_html=True)

    if all([off_market_file, sold_file, for_sale_file]):
        try:
            # Load and process data
            with st.spinner('Processing data...'):
                off_market_df = load_and_clean_data(off_market_file)
                sold_df = load_and_clean_data(sold_file)
                for_sale_df = load_and_clean_data(for_sale_file)
                
                # Find expired unlisted properties
                expired_unlisted = find_expired_unlisted_properties(
                    off_market_df, sold_df, for_sale_df
                )
                
                # Prepare data for display
                display_df = prepare_display_data(expired_unlisted)
                
                # Display results
                st.markdown("### Analysis Results")
                st.markdown(f"""
                <div style='background-color: #48BB78; color: white; padding: 1rem; 
                border-radius: 4px; margin-bottom: 1rem;'>
                    Found {len(display_df)} expired properties not currently listed or sold
                </div>
                """, unsafe_allow_html=True)
                
                # Add filters
                st.markdown("### Filters")
                col1, col2 = st.columns(2)
                with col1:
                    min_price = st.number_input(
                        "Minimum Price",
                        value=0,
                        step=50000
                    )
                with col2:
                    max_price = st.number_input(
                        "Maximum Price",
                        value=int(expired_unlisted['List Price'].max()),
                        step=50000
                    )
                
                # Apply filters
                filtered_df = display_df[
                    (expired_unlisted['List Price'] >= min_price) &
                    (expired_unlisted['List Price'] <= max_price)
                ]
                
                # Display results
                st.dataframe(
                    filtered_df,
                    use_container_width=True,
                    height=400
                )
                
                # Export functionality
                if not filtered_df.empty:
                    csv = export_to_csv(filtered_df)
                    b64 = base64.b64encode(csv.encode()).decode()
                    href = f'<a href="data:file/csv;base64,{b64}" download="expired_listings.csv" \
                        class="stButton">Download Results</a>'
                    st.markdown(href, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"Error processing files: {str(e)}")
    
    else:
        st.info("Please upload all three CSV files to begin analysis.")

if __name__ == "__main__":
    main()
