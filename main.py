import os

# Streamlit configuration
port = int(os.environ.get("PORT", 8501))

import streamlit as st
import pandas as pd
import base64
from utils import (
    load_and_clean_data,
    find_expired_unlisted_properties,
    prepare_display_data,
    export_to_csv,
    apply_filters
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

# Update the JavaScript section
st.markdown("""
<script>
document.addEventListener('DOMContentLoaded', function() {
    const tables = document.getElementsByTagName('table');
    Array.from(tables).forEach(table => {
        if (!table) return;

        const headers = table.querySelectorAll('th');
        const sortStates = new Array(headers.length).fill(null);

        headers.forEach((header, index) => {
            if (index === 0) return; // Skip MLS Link column

            header.style.cursor = 'pointer';
            header.addEventListener('click', () => {
                // Toggle sort state: null -> asc -> desc -> null
                if (sortStates[index] === null) {
                    sortStates[index] = 'asc';
                } else if (sortStates[index] === 'asc') {
                    sortStates[index] = 'desc';
                } else {
                    sortStates[index] = null;
                }

                // Reset other columns
                sortStates.forEach((state, i) => {
                    if (i !== index) sortStates[i] = null;
                });

                const rows = Array.from(table.querySelectorAll('tr:not(:first-child)'));

                if (sortStates[index] !== null) {
                    rows.sort((rowA, rowB) => {
                        const cellA = rowA.cells[index].textContent.trim();
                        const cellB = rowB.cells[index].textContent.trim();

                        // Parse numbers (including currency)
                        const numA = parseFloat(cellA.replace(/[^0-9.-]+/g, ''));
                        const numB = parseFloat(cellB.replace(/[^0-9.-]+/g, ''));

                        if (!isNaN(numA) && !isNaN(numB)) {
                            return sortStates[index] === 'asc' ? numA - numB : numB - numA;
                        }

                        return sortStates[index] === 'asc' 
                            ? cellA.localeCompare(cellB)
                            : cellB.localeCompare(cellA);
                    });
                }

                // Update header styles
                headers.forEach((h, i) => {
                    h.classList.remove('sorted-asc', 'sorted-desc');
                    if (i === index && sortStates[i] !== null) {
                        h.classList.add(`sorted-${sortStates[i]}`);
                    }
                });

                // Reorder rows
                const tbody = table.querySelector('tbody') || table;
                rows.forEach(row => tbody.appendChild(row));
            });
        });
    });
});
</script>
""", unsafe_allow_html=True)

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

                # Price filters
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

                # Property Type filter
                if 'Property Type' in expired_unlisted.columns:
                    property_types = sorted(expired_unlisted['Property Type'].dropna().unique())
                    selected_property_types = st.multiselect(
                        "Property Types",
                        options=property_types,
                        default=property_types
                    )

                # Other filters (beds, baths, DOM)
                col1, col2, col3 = st.columns(3)

                with col1:
                    valid_beds = sorted([int(x) for x in expired_unlisted['Bedrooms'].dropna().unique() if x > 0])
                    min_beds, max_beds = st.select_slider(
                        "Bedrooms Range",
                        options=valid_beds,
                        value=(min(valid_beds) if valid_beds else 0, max(valid_beds) if valid_beds else 0)
                    )

                with col2:
                    valid_baths = sorted([int(x) for x in expired_unlisted['Bathrooms'].dropna().unique() if x > 0])
                    min_baths, max_baths = st.select_slider(
                        "Bathrooms Range",
                        options=valid_baths,
                        value=(min(valid_baths) if valid_baths else 0, max(valid_baths) if valid_baths else 0)
                    )

                with col3:
                    valid_dom = sorted([int(x) for x in expired_unlisted['Days on Market'].dropna().unique() if x >= 0])
                    min_dom, max_dom = st.select_slider(
                        "Days on Market Range",
                        options=valid_dom,
                        value=(min(valid_dom) if valid_dom else 0, max(valid_dom) if valid_dom else 0)
                    )

                # Create filters dictionary
                filters = {
                    'min_price': min_price,
                    'max_price': max_price,
                    'min_beds': min_beds,
                    'max_beds': max_beds,
                    'min_baths': min_baths,
                    'max_baths': max_baths,
                    'min_dom': min_dom,
                    'max_dom': max_dom
                }

                if 'Property Type' in expired_unlisted.columns:
                    filters['property_types'] = selected_property_types

                # Apply filters
                filtered_df = apply_filters(display_df, expired_unlisted, filters)

                # Display results
                if not filtered_df.empty:
                    st.write(
                        filtered_df.to_html(escape=False, index=False),
                        unsafe_allow_html=True
                    )

                    # Export functionality
                    csv = export_to_csv(filtered_df)
                    b64 = base64.b64encode(csv.encode()).decode()
                    href = f'<a href="data:file/csv;base64,{b64}" download="expired_listings.csv" \
                        class="stButton">Download Results</a>'
                    st.markdown(href, unsafe_allow_html=True)
                else:
                    st.warning("No properties match the selected filters.")

        except Exception as e:
            st.error(f"Error processing files: {str(e)}")

    else:
        st.info("Please upload all three CSV files to begin analysis.")

if __name__ == "__main__":
    main()
