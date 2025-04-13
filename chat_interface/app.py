import os
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory, session
from werkzeug.utils import secure_filename
import logging
# Import utility functions
from pdf_utils import get_pdf_fields, fill_pdf_form
from gemini_utils import extract_data_for_pdf
from pypdf.generic import NameObject # Import NameObject
# from gemini_utils import extract_data_for_pdf

logging.basicConfig(level=logging.INFO)

# --- Flask App Setup ---
app = Flask(__name__)
app.secret_key = os.urandom(24) # Needed for session management

# Configuration (can be moved to a config file later)
# Define allowed extensions for security
ALLOWED_EXTENSIONS = {'pdf', 'csv'}

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DOWNLOAD_FOLDER'] = 'downloads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16 MB limit for uploads

# Ensure upload and download directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)


# --- Routes ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Routes ---
@app.route('/')
def index():
    """Serves the main chat interface page. Clears session on new visit."""
    session.clear() # Clear previous PDF info on new visit
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles PDF/CSV file uploads."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        # Generate a unique filename to avoid conflicts
        unique_suffix = uuid.uuid4().hex[:8]
        unique_filename = f"{os.path.splitext(original_filename)[0]}_{unique_suffix}{os.path.splitext(original_filename)[1]}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

        try:
            file.save(filepath)
            logging.info(f"File '{original_filename}' saved as '{unique_filename}'")

            file_extension = original_filename.rsplit('.', 1)[1].lower()

            if file_extension == 'pdf':
                # Process PDF: Extract fields
                fields = get_pdf_fields(filepath)
                if fields is None: # Check if get_pdf_fields indicated an error (e.g., returned None or threw exception handled inside)
                   logging.error(f"Failed to extract fields from PDF: {unique_filename}")
                   # Store minimal info even if fields couldn't be extracted
                   session['current_pdf_path'] = filepath
                   session['current_pdf_filename'] = original_filename
                   session['current_pdf_fields'] = {} # Store empty dict
                   return jsonify({
                       "message": f"File '{original_filename}' uploaded, but failed to extract form fields.",
                       "filename": original_filename,
                       "fields": {}
                   }), 500 # Internal Server Error might be appropriate

                # Store info in session for later use
                session['current_pdf_path'] = filepath
                session['current_pdf_filename'] = original_filename
                session['current_pdf_fields'] = fields # Store extracted fields

                logging.info(f"Extracted fields for {original_filename}: {fields}")
                return jsonify({
                    "message": f"File '{original_filename}' uploaded successfully.",
                    "filename": original_filename,
                    "fields": fields
                })
            elif file_extension == 'csv':
                # Store info for later processing
                session['current_csv_path'] = filepath
                session['current_csv_filename'] = original_filename
                session.pop('current_pdf_path', None) # Clear PDF info if CSV is uploaded
                session.pop('current_pdf_filename', None)
                session.pop('current_pdf_fields', None)

                logging.info(f"CSV file {original_filename} uploaded. Ready for batch processing.")
                # TODO: Implement CSV processing logic later
                return jsonify({
                    "message": f"CSV file '{original_filename}' uploaded. Batch processing not yet implemented.",
                    "filename": original_filename,
                    "type": "csv"
                })

        except Exception as e:
            logging.error(f"Error uploading or processing file {original_filename}: {e}", exc_info=True)
            # Clean up saved file if processing failed
            if os.path.exists(filepath):
                 try:
                     os.remove(filepath)
                 except OSError as rm_err:
                     logging.error(f"Error removing failed upload file {filepath}: {rm_err}")
            return jsonify({"error": f"An error occurred: {e}"}), 500

    else:
        return jsonify({"error": "File type not allowed"}), 400


@app.route('/chat', methods=['POST'])
def chat():
    """Handles incoming chat messages."""
    data = request.get_json()
    user_message = data.get('message')

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    bot_response = "I received your message." # Default response
    extracted_data = None
    filled_pdf_info = None # Will store {'filename': ..., 'url': ...}

    # Check if a PDF is loaded (info stored in session)
    current_pdf_path = session.get('current_pdf_path')
    current_pdf_filename = session.get('current_pdf_filename')
    current_pdf_fields = session.get('current_pdf_fields')

    if current_pdf_path and current_pdf_filename and current_pdf_fields:
        logging.info(f"Processing message for PDF: {current_pdf_filename}")
        # Attempt to extract data using Gemini
        extracted_data = extract_data_for_pdf(user_message, list(current_pdf_fields.keys()))

        if not extracted_data:
            bot_response = "I couldn't extract relevant information from your message for the loaded PDF."
        else:
            logging.info(f"Gemini extracted: {extracted_data}")

            # --- Post-process Gemini data for checkboxes ---
            fill_data = {}
            for key, value in extracted_data.items():
                if value is None:
                    continue # Skip null values

                # Check if the field is a known button type from the session
                field_type = current_pdf_fields.get(key)
                if field_type == '/Btn':
                    # If Gemini returned *any* non-empty string for a button, assume it should be checked
                    # More sophisticated logic could be added here if needed (e.g., check for specific keywords)
                    if isinstance(value, str) and value.strip() != "":
                        fill_data[key] = NameObject("/Yes") # Replace string with NameObject('/Yes')
                        logging.debug(f"Converted Gemini value for checkbox '{key}' to NameObject('/Yes')")
                    else:
                        # If Gemini returned something other than a string (or empty string), skip
                        logging.debug(f"Skipping checkbox '{key}': Gemini value '{value}' not interpreted as 'check'.")
                else:
                    # For non-button fields, keep the original extracted value
                    fill_data[key] = value
            # --- End post-processing ---

            logging.info(f"Data after post-processing for checkboxes: {fill_data}")

            if not fill_data:
                 bot_response = "I extracted some data, but none of it seems directly applicable to fill the form fields based on your message."
            else:
                # Attempt to fill the PDF
                base_name = os.path.splitext(current_pdf_filename)[0]
                output_suffix = uuid.uuid4().hex[:8]
                output_filename = f"{base_name}_filled_{output_suffix}.pdf"
                output_filepath = os.path.join(app.config['DOWNLOAD_FOLDER'], output_filename)

                try:
                    logging.info(f"Attempting to fill PDF '{current_pdf_path}' with data: {fill_data}") # Log the data being passed
                    success = fill_pdf_form(current_pdf_path, output_filepath, fill_data)
                    if success:
                        bot_response = f"Okay, I've extracted the data and attempted to fill the PDF '{current_pdf_filename}'. You can download it now." # Changed wording slightly
                        # Generate a URL for the download route
                        download_url = f"/download/{output_filename}"
                        filled_pdf_info = {"filename": output_filename, "url": download_url}
                        logging.info(f"PDF filled successfully: {output_filename}")
                    else:
                        bot_response = "I extracted the data, but encountered an error while trying to fill the PDF."
                        logging.error(f"Failed to fill PDF for {current_pdf_filename}")

                except Exception as e:
                    bot_response = f"An unexpected error occurred during PDF filling: {e}"
                    logging.error(f"Unexpected error filling PDF {current_pdf_filename}: {e}", exc_info=True)

    else:
        # No PDF loaded, just acknowledge the message
        bot_response = "I received your message. Please upload a PDF form if you want me to fill it."
        logging.info("Received chat message, but no PDF loaded in session.")


    return jsonify({
        "bot_message": bot_response,
        "extracted_data": extracted_data, # Send extracted data back for display
        "filled_pdf": filled_pdf_info # Send download info if created
    })


@app.route('/download/<filename>')
def download_file(filename):
    """Serves files from the download folder."""
    # Sanitize filename just in case, although UUIDs should be safe
    safe_filename = secure_filename(filename)
    try:
        return send_from_directory(app.config['DOWNLOAD_FOLDER'], safe_filename, as_attachment=True)
    except FileNotFoundError:
        logging.error(f"Download request for non-existent file: {safe_filename}")
        return jsonify({"error": "File not found"}), 404


# --- Run the App ---
if __name__ == '__main__':
    # Note: Setting debug=True is convenient for development but should be False in production
    app.run(debug=True, port=5001) # Using port 5001 to avoid potential conflicts