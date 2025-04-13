import google.generativeai as genai
import os
import google.generativeai as genai
import os
import logging
import json
from dotenv import load_dotenv
from pypdf.generic import NameObject # Import NameObject

logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.0-flash" # As requested

if not API_KEY:
    logging.warning("GEMINI_API_KEY environment variable not set. Gemini features will not work.")
    # raise ValueError("GEMINI_API_KEY environment variable not set.") # Or raise error immediately
else:
    try:
        genai.configure(api_key=API_KEY)
        logging.info("Gemini API configured successfully.")
    except Exception as e:
        logging.error(f"Error configuring Gemini API: {e}", exc_info=True)
        API_KEY = None # Prevent further attempts if configuration fails

# --- Core Function ---

def extract_data_for_pdf(text: str, fields: list[str]) -> dict:
    """
    Uses Gemini to extract structured data from text based on desired PDF fields.

    Args:
        text: The natural language input text containing information.
        fields: A list of field names to extract data for.

    Returns:
        A dictionary mapping field names to extracted values.
        Returns an empty dictionary if the API key is not set or an error occurs.
    """
    if not API_KEY:
        logging.error("Gemini API key not configured. Cannot extract data.")
        return {}

    if not text or not fields:
        logging.warning("No text or fields provided for extraction.")
        return {}

    # Construct the prompt for Gemini, requesting JSON output
    # Identify potential checkbox fields (this might need refinement based on exact field names)
    # We assume fields that are just drug names or condition names might be checkboxes
    potential_checkbox_fields = [
        field for field in fields
        if field in ["Xeljanz", "Xeljanz XR", "Cimzia", "Rheumatoid Arthritis", "CPSA", "AHS", # Add other known checkbox fields
                     "Abatacept", "Actemra", "Adalimumab", "Amgevita", "Avsola", "Brenzys",
                     "Certilizumab", "Erelzi", "Etanercept", "Golimumab", "Hadlima", "Hulio",
                     "Hyrimoz", "Idacio", "Inflectra", "Infliximab", "Ixifi", "Kevzara", "Kineret",
                     "Olumiant", "Orencia", "Remdantry", "Remsima SC2", "Renflexis", "Rinvoq",
                     "Rituximab", "Rymti", "Sarilumab", "Simlandi", "Simponi", "Tocilizumab", "Yuflyma"]
                     # Add conditions if they are separate fields like "Psoriatic Arthritis" etc.
    ]

    json_schema_example = {}
    for field in fields:
        if field in potential_checkbox_fields:
            json_schema_example[field] = '"CHECKED" or null' # Special marker for checkboxes
        else:
            json_schema_example[field] = "extracted string value or null"


    prompt = f"""
Extract the relevant information from the following text to fill the specified fields.
Provide the output strictly as a JSON object with keys corresponding exactly to the field names provided.

Instructions:
- For regular text fields (like names, dates, addresses, dosages), extract the corresponding value from the text. If not found, use JSON null.
- For fields that represent a selection or checkbox (like specific drug names or conditions listed in the 'Potential Checkbox Fields'), determine if the text indicates this option should be selected/checked.
- If a checkbox field should be checked/selected based on the text, use the exact string "CHECKED" as its value in the JSON.
- If a checkbox field should NOT be checked/selected, use JSON null as its value.

Desired Fields: {json.dumps(fields)}
Potential Checkbox Fields: {json.dumps(potential_checkbox_fields)}

Example JSON Output Format: {json.dumps(json_schema_example, indent=2)}

Input Text:
---
{text}
---

JSON Output (strictly JSON, no surrounding text):
"""

    try:
        model = genai.GenerativeModel(
            MODEL_NAME,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json" # Enable JSON mode
            )
        )
        response = model.generate_content(prompt)

        # Debugging: Print raw response text
        logging.debug(f"Gemini Raw Response: {response.text}")

        # Parse the JSON response
        extracted_data = json.loads(response.text)

        # Basic validation: Check if it's a dictionary
        if not isinstance(extracted_data, dict):
            logging.error(f"Gemini response was not a valid JSON object: {response.text}")
            return {}

        # Filter to only include requested fields and handle potential extra fields from Gemini
        # Also, convert "CHECKED" marker to NameObject("/Yes")
        result_data = {}
        for field in fields:
            value = extracted_data.get(field)
            if value == "CHECKED":
                result_data[field] = NameObject("/Yes") # Use NameObject for checked boxes
                logging.debug(f"Converted field '{field}' marker 'CHECKED' to NameObject('/Yes')")
            else:
                # Keep null or extracted string value
                result_data[field] = value

        logging.info(f"Successfully extracted and processed data using Gemini: {result_data}")
        return result_data

    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON response from Gemini: {e}\nRaw response: {response.text}", exc_info=True)
        return {}
    except Exception as e:
        logging.error(f"Error calling Gemini API: {e}", exc_info=True)
        return {}

# --- Example Usage ---
if __name__ == '__main__':
    if not API_KEY:
        print("\nSkipping Gemini example usage as API key is not configured.")
    else:
        print("-" * 20)
        print("Testing Gemini data extraction...")
        sample_text = """
        Patient Name: John Doe, DOB: 1985-03-15. Prescriber: Dr. Alice Smith, Reg #: 12345.
        Diagnosis: Rheumatoid Arthritis. Requested Drug: Humira. Weight: 75kg.
        Previous Meds: Methotrexate PO for 6 months, no response.
        """
        # Example fields based on 'ABC SA Form.pdf' (adjust as needed)
        sample_fields = [
            "PATIENT LAST NAME",
            "FIRST NAME",
            "BIRTH DATE (YYYY-MM-DD)",
            "PRESCRIBER LAST NAME",
            "REGISTRATION NUMBER",
            "Diagnosis",
            "Indicate requested drug", # This might need refinement based on actual field name
            "Current weight (kg)",
            "Methotrexate PO" # Represents the text field for previous meds
        ]

        extracted = extract_data_for_pdf(sample_text, sample_fields)

        if extracted:
            print("\nExtracted Data:")
            for key, value in extracted.items():
                print(f"  {key}: {value}")
        else:
            print("\nFailed to extract data using Gemini.")
        print("-" * 20)
