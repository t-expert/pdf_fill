import logging
from pdf_utils import get_pdf_fields # Re-use the function to get field details
from pypdf import PdfReader
from pypdf.generic import NameObject

logging.basicConfig(level=logging.INFO)

# --- Configuration ---
# Point this to the PDF you MANUALLY edited and saved
# Assuming it's the one from the first successful test run
PDF_TO_READ = 'test_filled_output.pdf'
FIELD_TO_CHECK = 'Xeljanz' # The field you manually checked

# --- Read Logic ---
if __name__ == "__main__":
    logging.info(f"--- Reading Field Value ---")
    logging.info(f"Reading PDF: {PDF_TO_READ}")
    logging.info(f"Checking field: {FIELD_TO_CHECK}")

    try:
        reader = PdfReader(PDF_TO_READ)
        fields = reader.get_fields()

        if not fields:
            logging.error("Could not read fields from the PDF.")
        elif FIELD_TO_CHECK not in fields:
            logging.error(f"Field '{FIELD_TO_CHECK}' not found in the PDF fields.")
            logging.info(f"Available fields: {list(fields.keys())}")
        else:
            # Find the specific field object
            field_data = fields[FIELD_TO_CHECK]
            field_value = field_data.get('/V') # Get the value key

            logging.info(f"Raw field data for '{FIELD_TO_CHECK}': {field_data}")
            logging.info(f"Value (/V) found for '{FIELD_TO_CHECK}': {field_value} (Type: {type(field_value)})")

            if isinstance(field_value, NameObject):
                 logging.info(f"RECOMMENDATION: Try using NameObject('{field_value}') in the test script for this checkbox.")
            else:
                 logging.info("The value is not a NameObject. Further investigation might be needed if this was a checkbox.")

    except FileNotFoundError:
        logging.error(f"PDF file not found: {PDF_TO_READ}")
    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)

    logging.info(f"--- Read Script Finished ---")