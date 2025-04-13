import logging
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, BooleanObject, TextStringObject # Import necessary objects

logging.basicConfig(level=logging.INFO)

def get_pdf_fields(pdf_path: str) -> dict:
    """
    Extracts form field names and types from a PDF file.

    Args:
        pdf_path: The path to the PDF file.

    Returns:
        A dictionary where keys are field names and values are field types (e.g., '/Tx' for text).
        Returns an empty dictionary if no fields are found or an error occurs.
    """
    fields = {}
    try:
        reader = PdfReader(pdf_path)
        pdf_fields = reader.get_fields()

        if not pdf_fields:
            logging.info(f"No form fields found in {pdf_path}")
            return {}

        for field_key, field_data in pdf_fields.items():
            # '/T' usually holds the field name
            field_name = field_data.get('/T')
            # '/FT' holds the field type (e.g., '/Tx', '/Btn', '/Ch')
            field_type = field_data.get('/FT')
            if field_name:
                fields[field_name] = field_type if field_type else 'Unknown'
                # Log extra details for button fields to find export value
                if field_type == '/Btn':
                    logging.debug(f"Button Field Details for '{field_name}': {field_data}")
            else:
                logging.warning(f"Field found without a name (key: {field_key}) in {pdf_path}")

        logging.info(f"Extracted fields from {pdf_path}: {fields}")
        return fields

    except FileNotFoundError:
        logging.error(f"PDF file not found at {pdf_path}")
        return {}
    except Exception as e:
        logging.error(f"Error reading PDF fields from {pdf_path}: {e}", exc_info=True)
        return {}

def fill_pdf_form(input_pdf_path: str, output_pdf_path: str, data: dict) -> bool:
    """
    Fills a PDF form with the provided data.

    Args:
        input_pdf_path: Path to the original PDF form.
        output_pdf_path: Path where the filled PDF should be saved.
        data: A dictionary where keys are field names and values are the data to fill.

    Returns:
        True if filling was successful, False otherwise.
    """
    reader = None # Initialize reader outside try block for potential cleanup
    try:
        reader = PdfReader(input_pdf_path)
        fields = reader.get_fields()

        if not fields:
            logging.warning(f"No fields found in {input_pdf_path} via get_fields(). Cannot fill.")
            # Still try to copy the file as is? Or return False? Let's return False.
            return False

        # --- Modify Reader's Field Values Directly ---
        logging.info(f"Attempting to update reader fields with data: {data}")
        updated_count = 0
        # Get the actual AcroForm dictionary object
        acro_form_ref = reader.trailer["/Root"].get(NameObject("/AcroForm"))
        if acro_form_ref:
             acro_form = acro_form_ref.get_object() # Get the actual dictionary
             # Set /NeedAppearances on the actual dictionary object
             acro_form[NameObject("/NeedAppearances")] = BooleanObject(True)
             logging.info("Set /NeedAppearances = true in reader's AcroForm")

             # Iterate through fields in the AcroForm structure
             # Iterate through fields in the AcroForm structure (using the actual dictionary)
             form_fields = acro_form.get(NameObject("/Fields"), [])
             field_map = {field.get(NameObject("/T")): field for field in form_fields if NameObject("/T") in field} # Map name to field object

             for key, value in data.items():
                 if key in field_map:
                     field_ref = field_map[key]
                     field_obj = field_ref.get_object() # Ensure we have the actual object

                     # Check field type to handle buttons correctly
                     field_type = field_obj.get(NameObject("/FT"))

                     if field_type == NameObject("/Btn"):
                         # For buttons (checkboxes/radio), set /V and /AS to the NameObject value
                         if isinstance(value, NameObject): # Ensure the value is a NameObject (like NameObject('/On'))
                             field_obj[NameObject("/V")] = value
                             field_obj[NameObject("/AS")] = value # Set Appearance State too
                             logging.debug(f"Updated Button field '{key}' with value/state '{value}'")
                         else:
                             logging.warning(f"Skipping button field '{key}': Value '{value}' is not a NameObject.")
                     elif field_type == NameObject("/Tx"):
                         # For text fields, wrap the value in TextStringObject
                         field_obj[NameObject("/V")] = TextStringObject(str(value))
                         logging.debug(f"Updated Text field '{key}' with value '{value}'")
                     else:
                         # Handle other field types if necessary, or just try setting as text
                         logging.warning(f"Attempting to set value for unhandled field type '{field_type}' for key '{key}'. Treating as text.")
                         field_obj[NameObject("/V")] = TextStringObject(str(value))

                     updated_count += 1
                 else:
                     logging.warning(f"Field '{key}' from data not found in PDF form fields.")
        else:
             logging.error(f"Could not find /AcroForm in {input_pdf_path}. Cannot fill.")
             return False

        if updated_count == 0:
            logging.warning("No matching fields found to update.")
            # Decide if this is an error or just means no data matched
            # Let's proceed and write the (potentially unchanged) file

        # --- Write the Modified Reader to a New Writer ---
        writer = PdfWriter()
        # Add pages from the modified reader
        writer.append(reader) # append() is often better for copying full structure

        # Write the output
        logging.info(f"Writing filled PDF to {output_pdf_path}")
        with open(output_pdf_path, "wb") as output_stream:
            writer.write(output_stream)

        logging.info(f"Successfully wrote filled PDF: {output_pdf_path}")
        return True

    except FileNotFoundError:
        logging.error(f"Input PDF file not found at {input_pdf_path}")
        return False
    except Exception as e:
        logging.error(f"Error during PDF filling process for {input_pdf_path}: {e}", exc_info=True)
        return False
    finally:
        # Ensure the reader file handle is closed if it was opened
        if reader and hasattr(reader, 'stream') and not reader.stream.closed:
             try:
                 reader.stream.close()
                 logging.debug("Closed PdfReader stream.")
             except Exception as close_err:
                 logging.error(f"Error closing PdfReader stream: {close_err}")
                     # Optionally update appearance stream (/AP) if needed, but /NeedAppearances should handle it
                     # field_obj[NameObject("/AP")] = ...


if __name__ == '__main__':
    # Example usage (requires a sample form PDF in the parent directory)
    sample_pdf = '../ABC SA Form.pdf' # Adjust path if needed

    print("-" * 20)
    print("Testing get_pdf_fields...")
    extracted_fields = get_pdf_fields(sample_pdf)
    if extracted_fields:
        print("Extracted Fields:")
        for name, ftype in extracted_fields.items():
            print(f"  Name: {name}, Type: {ftype}")

        print("-" * 20)
        print("Testing fill_pdf_form...")
        # Example data - adjust field names based on actual extracted fields
        test_data = {
            # Replace with actual field names from your PDF
            list(extracted_fields.keys())[0]: "Test Value 1",
            list(extracted_fields.keys())[1]: "Test Value 2",
            # Add more fields as needed
        }
        output_file = 'filled_test_form.pdf' # Will be saved in chat_interface dir
        success = fill_pdf_form(sample_pdf, output_file, test_data)
        if success:
            print(f"Successfully created filled PDF: {output_file}")
        else:
            print(f"Failed to create filled PDF.")

    else:
        print(f"Could not extract fields from {sample_pdf}, skipping fill test.")