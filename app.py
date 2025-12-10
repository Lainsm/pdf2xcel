import streamlit as st
import camelot
import pandas as pd
import io
import os

# --- 1. Camelot Table Extraction Function ---
def extract_tables_to_excel(pdf_file_buffer, flavor, pages):
    """
    Extracts tables from a PDF file buffer using Camelot and returns the 
    Excel file data as a bytes buffer.
    """
    # 1. Save the uploaded file buffer temporarily to a file
    temp_pdf_path = "temp_uploaded_file.pdf"
    try:
        with open(temp_pdf_path, "wb") as f:
            # st.session_state is often used but getbuffer() is simpler here
            f.write(pdf_file_buffer.getbuffer()) 
            
        st.info(f"Using Camelot with flavor: **{flavor.upper()}** on pages: **{pages}**")

        tables = camelot.read_pdf(
            temp_pdf_path,
            pages=pages,
            flavor=flavor,
            # Ensure the table_areas parameter is None if empty to avoid errors
            # table_areas=None 
        )
        
    except Exception as e:
        st.error(f"Error reading PDF with Camelot: {e}")
        st.warning("Please ensure Ghostscript is correctly configured on the hosting server.")
        return None

    finally:
        # Clean up the temporary file
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)

    if len(tables) == 0:
        st.warning("No tables were extracted. Try switching the extraction **Flavor** (Lattice/Stream).")
        return None
    
    st.success(f"Successfully extracted **{len(tables)}** tables from the PDF.")

    # 2. Write DataFrames to Excel in a memory buffer
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:

        for i, table in enumerate(tables):
            df = table.df
            sheet_name = f'Table_P{table.page}_{i + 1}'
            df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
            
    excel_buffer.seek(0)
    return excel_buffer

# --- 2. Streamlit UI (User Interface) ---

st.set_page_config(
    page_title="PDF Table Extractor (Camelot)",
    layout="centered"
)

st.title("📚 PDF Table Extractor")
st.markdown("Upload your PDF, select settings, and click **Extract**.")


# --- Sidebar Configuration ---
st.sidebar.header("⚙️ Extraction Settings")

# Flavor selection
flavor_options = ('stream', 'lattice')
selected_flavor = st.sidebar.selectbox(
    "1. Select Camelot Flavor:",
    options=flavor_options,
    index=0, 
    help="Lattice relies on lines (slower). Stream relies on whitespace (faster)."
)

# Pages selection
selected_pages = st.sidebar.text_input(
    "2. Specify Pages (e.g., 1,2,5 or all):",
    value='all',
    help="Use 'all' for all pages, or comma-separated page numbers/ranges (e.g., 1,3-5)."
)

st.sidebar.markdown("---")


# --- Main Uploader Area ---
uploaded_file = st.file_uploader(
    "Choose a PDF file to upload", 
    type="pdf"
)

# ==============================================================================
# 🌟 KEY CHANGE: Check if file is uploaded AND the button is pressed
# ==============================================================================

# Place the button inside a container or under a condition for clarity
if uploaded_file is not None:
    st.markdown("### Ready to Extract")
    
    # Add the button
    if st.button("🚀 Start Table Extraction"):
        st.markdown("---")
        
        # Run the extraction function only when the button is pressed
        excel_data_buffer = extract_tables_to_excel(
            uploaded_file, 
            flavor=selected_flavor, 
            pages=selected_pages
        )
        
        st.markdown("---")

        if excel_data_buffer:
            # Provide the download button
            st.download_button(
                label="✅ Download Extracted Data as Excel",
                data=excel_data_buffer,
                file_name=uploaded_file.name.replace(".pdf", f"_{selected_flavor}_extracted.xlsx"),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            # This covers the case where extraction failed or no tables were found
            st.error("Extraction process completed, but no data was returned.")
            
# The code below only runs if a file is NOT yet uploaded
else:
    st.info("Awaiting PDF file upload...")
