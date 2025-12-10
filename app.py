import streamlit as st
import camelot
import pandas as pd
import io
import os


# --- 1. Camelot Table Extraction Function ---
# This is the core logic, adapted to take a file buffer from Streamlit
def extract_tables_to_excel(pdf_file_buffer, flavor='stream', pages='all'):
    """
    Extracts tables from a PDF file buffer using Camelot and returns the
    Excel file data as a bytes buffer.
    """

    # 1. Read Tables using Camelot
    # Camelot requires the PDF file path or a file-like object
    try:
        # Save the uploaded file buffer temporarily to a file
        temp_pdf_path = "temp_uploaded_file.pdf"
        with open(temp_pdf_path, "wb") as f:
            f.write(pdf_file_buffer.getbuffer())

        st.info(f"Using Camelot with flavor: **{flavor.upper()}** on pages: **{pages}**")

        tables = camelot.read_pdf(
            temp_pdf_path,
            pages=pages,
            flavor=flavor,
            # Adjust these parameters if needed:
            # edge_tol=500, # useful for stream
        )

    except Exception as e:
        st.error(f"Error reading PDF with Camelot: {e}")
        st.warning("Ensure Ghostscript is installed and accessible in your system's PATH if running locally.")
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
            # Access the underlying pandas DataFrame
            df = table.df

            # Use i + 1 for 1-based sheet numbering
            # P{table.page} gives the page number the table was found on
            sheet_name = f'Table_P{table.page}_{i + 1}'

            # Write the table (DataFrame) to a sheet
            df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
            # You can view the report if you want to inspect quality:
            # st.write(f"Sheet: {sheet_name} | Accuracy: {table.parsing_report['accuracy']}%")

    excel_buffer.seek(0)
    return excel_buffer


# --- 2. Streamlit UI (User Interface) ---

st.set_page_config(
    page_title="PDF Table Extractor (Camelot)",
    layout="centered"
)

st.title("📚 PDF Table Extractor")
st.markdown("Upload your PDF and use Camelot to extract tables directly into a downloadable Excel file.")

# --- Sidebar Configuration ---
st.sidebar.header("⚙️ Extraction Settings")

# Flavor selection
flavor_options = ('stream', 'lattice')
selected_flavor = st.sidebar.selectbox(
    "1. Select Camelot Flavor:",
    options=flavor_options,
    index=0,  # 'stream' is often better for general data
    help="Lattice works best for tables with lines. Stream works best for tables with large white spaces separating columns."
)

# Pages selection
selected_pages = st.sidebar.text_input(
    "2. Specify Pages (e.g., 1,2,5 or all):",
    value='all',
    help="Use 'all' for all pages, or comma-separated page numbers/ranges (e.g., 1,3-5)."
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Need Help?** Try switching the Flavor if extraction fails.")

# --- Main Uploader Area ---
uploaded_file = st.file_uploader(
    "Choose a PDF file to upload",
    type="pdf"
)

if uploaded_file is not None:
    st.markdown("### Extraction Result")

    # Run the extraction function
    excel_data_buffer = extract_tables_to_excel(
        uploaded_file,
        flavor=selected_flavor,
        pages=selected_pages
    )

    if excel_data_buffer:
        # Provide the download button
        st.download_button(
            label="⬇️ Download Extracted Data as Excel",
            data=excel_data_buffer,
            file_name=uploaded_file.name.replace(".pdf", "_extracted.xlsx"),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("Extraction failed or no tables were found.")