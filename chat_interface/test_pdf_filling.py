# Configure logging FIRST
import logging
# Configure logging to write directly to a file
log_filename = 'test_run.log'
logging.basicConfig(
    filename=log_filename,
    filemode='w', # Overwrite previous log file
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logging.debug("Logging configured to write to file.")

import os
from pdf_utils import fill_pdf_form
from pypdf.generic import NameObject

# --- Configuration ---
INPUT_PDF = '../ABC SA Form.pdf'
OUTPUT_DIR = '.' # Output in chat_interface directory

# --- Test Cases ---
# Each dictionary contains 'suffix' for filename and 'data' for filling
TEST_CASES = [
    {
        "suffix": "case1_basic",
        "data": {
            "LName": "CaseOne", "FName": "Basic", "Address": "1 Main St", "City": "Anytown",
            "Birth Date_af_date": "1995-05-10", "Prov": "ON", "PCode": "A1A 1A1"
        }
    },
    {
        "suffix": "case2_prescriber",
        "data": {
            "LName": "CaseTwo", "FName": "Prescriber", "Prescriber LName": "Smith", "Prescriber FName": "Alice",
            "Prescriber RegNo": "11223", "Prescriber Phone": "555-1234", "CPSA": NameObject("/Yes") # Use /Yes based on reader script & logs
        }
    },
    {
        "suffix": "case3_meds",
        "data": {
            "LName": "CaseThree", "FName": "Meds", "Current weight (kg)": "80", "Dosage": "10mg daily",
            "Xeljanz": NameObject("/Yes"), # Use /Yes based on reader script
            "Rheumatoid Arthritis": NameObject("/Yes") # Use /Yes based on reader script & logs
        }
    },
    {
        "suffix": "case4_mixed",
        "data": {
            "LName": "CaseFour", "FName": "Mixed", "Birth Date_af_date": "1988-11-22", "Address": "456 Side Rd",
            "City": "Otherville", "Prov": "BC", "PCode": "V2V 2V2", "PHN": "987654321",
            "Prescriber LName": "Jones", "Prescriber FName": "Bob", "Prescriber RegNo": "44556",
            "Current weight (kg)": "65", "Dosage": "20mg twice daily",
            "Cimzia": NameObject("/Yes"), # Use /Yes based on logs
            "AHS": NameObject("/Yes") # Use /Yes based on logs
        }
    },
    # Add more test cases as needed
]

# --- Test Execution ---
if __name__ == "__main__":
    logging.info(f"--- Starting Multiple PDF Fill Tests ---")
    logging.info(f"Input PDF: {INPUT_PDF}")
    logging.info(f"Output Directory: {OUTPUT_DIR}")

    if not os.path.exists(INPUT_PDF):
        logging.error(f"Input PDF not found at expected location: {os.path.abspath(INPUT_PDF)}")
        logging.error("Please ensure 'ABC SA Form.pdf' is in the parent directory ('Gemini_PDF fill').")
        exit()

    # Optional: Get fields once if needed for reference (already logged in previous runs)
    # from pdf_utils import get_pdf_fields
    # logging.info("--- Getting Field Details ---")
    # fields = get_pdf_fields(INPUT_PDF)
    # logging.info("--- Finished Getting Field Details ---")

    all_tests_passed = True
    for i, case in enumerate(TEST_CASES):
        suffix = case["suffix"]
        data = case["data"]
        output_filename = f"test_filled_output_{suffix}.pdf"
        output_filepath = os.path.join(OUTPUT_DIR, output_filename)

        logging.info(f"\n--- Running Test Case {i+1}: {suffix} ---")
        logging.info(f"Output File: {output_filepath}")
        logging.info(f"Data: {data}")

        success = fill_pdf_form(INPUT_PDF, output_filepath, data)

        if success:
            logging.info(f"Test Case {i+1} Completed Successfully.")
            logging.info(f"Filled PDF saved to: {os.path.abspath(output_filepath)}")
        else:
            logging.error(f"Test Case {i+1} Failed.")
            logging.error("The fill_pdf_form function returned False. Check previous logs for errors.")
            all_tests_passed = False

    logging.info(f"\n--- All Test Cases Finished ---")
    if all_tests_passed:
        logging.info("All tests completed successfully according to function return values.")
    else:
        logging.warning("One or more test cases failed.")
    logging.info("Please manually verify the generated PDF files.")