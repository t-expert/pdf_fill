document.addEventListener('DOMContentLoaded', () => {
    console.log("AI PDF Filler script loaded.");

    // --- DOM Elements ---
    const messagesDiv = document.getElementById('messages');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const pdfUploadInput = document.getElementById('pdf-upload');
    const uploadButton = document.getElementById('upload-button');
    const uploadStatusSpan = document.getElementById('upload-status');
    const pdfInfoDiv = document.getElementById('pdf-info');
    const filledFieldsDiv = document.getElementById('filled-fields');
    const downloadLinksDiv = document.getElementById('download-links');

    // --- State ---
    let currentPdfFilename = null;
    let currentPdfFields = null;

    // --- Helper Functions ---
    function addMessage(text, sender = 'system') {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', sender); // sender can be 'user', 'bot', 'system'
        messageElement.textContent = text;
        messagesDiv.appendChild(messageElement);
        // Scroll to the bottom
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    function updatePdfInfo(filename, fields) {
        if (filename && fields) {
            currentPdfFilename = filename;
            currentPdfFields = fields;
            const fieldNames = Object.keys(fields).join(', ');
            pdfInfoDiv.innerHTML = `<strong>Loaded:</strong> ${filename}<br><strong>Fields:</strong> ${fieldNames || 'None found'}`;
        } else {
            currentPdfFilename = null;
            currentPdfFields = null;
            pdfInfoDiv.textContent = 'No PDF loaded.';
        }
    }

    function updateFilledFields(filledData) {
        if (filledData && Object.keys(filledData).length > 0) {
            let html = '<ul>';
            for (const [key, value] of Object.entries(filledData)) {
                html += `<li><strong>${key}:</strong> ${value !== null ? value : '<em>null</em>'}</li>`;
            }
            html += '</ul>';
            filledFieldsDiv.innerHTML = html;
        } else {
            filledFieldsDiv.textContent = 'No fields filled yet.';
        }
    }

     function addDownloadLink(filename, url) {
        const link = document.createElement('a');
        link.href = url;
        link.textContent = `Download ${filename}`;
        link.target = '_blank'; // Open in new tab
        // Optionally add download attribute: link.download = filename;
        downloadLinksDiv.appendChild(link);
    }

    function clearDownloads() {
        downloadLinksDiv.innerHTML = 'No downloads available.';
    }

    function setUploadStatus(message, isError = false) {
        uploadStatusSpan.textContent = message;
        uploadStatusSpan.style.color = isError ? 'red' : 'green';
    }

    // --- Event Listeners ---
    sendButton.addEventListener('click', handleSendMessage);
    messageInput.addEventListener('keypress', (event) => {
        // Allow sending with Enter key (Shift+Enter for newline)
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault(); // Prevent default newline behavior
            handleSendMessage();
        }
    });

    uploadButton.addEventListener('click', handleUpload);

    // --- Event Handlers ---
    function handleSendMessage() {
        const messageText = messageInput.value.trim();
        if (!messageText) return;

        addMessage(messageText, 'user');
        const thinkingMessage = addMessage("Thinking...", 'bot'); // Keep reference to update/remove later if needed

        messageInput.value = ''; // Clear input
        messageInput.disabled = true; // Disable input while processing
        sendButton.disabled = true;

        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: messageText }),
        })
        .then(response => {
            if (!response.ok) {
                 // Try to parse error message from JSON response
                 return response.json().then(errData => {
                    throw new Error(errData.error || `HTTP error! status: ${response.status}`);
                }).catch(() => {
                    // Fallback if response is not JSON or parsing fails
                    throw new Error(`HTTP error! status: ${response.status}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log("Chat response:", data);
            // Remove "Thinking..." message or update it
            if (thinkingMessage) thinkingMessage.remove(); // Simple removal

            // Display bot's main message
            if (data.bot_message) {
                addMessage(data.bot_message, 'bot');
            }

            // Update the filled fields display based on extracted_data
            // Note: extracted_data might contain nulls, updateFilledFields handles this
            if (data.extracted_data) {
                 updateFilledFields(data.extracted_data);
            }

            // Add download link if a PDF was filled
            if (data.filled_pdf && data.filled_pdf.url && data.filled_pdf.filename) {
                addDownloadLink(data.filled_pdf.filename, data.filled_pdf.url);
            }
        })
        .catch(error => {
            console.error('Chat error:', error);
             if (thinkingMessage) thinkingMessage.remove(); // Remove thinking message on error too
            addMessage(`Error: ${error.message}`, 'system');
        })
        .finally(() => {
            // Re-enable input fields
            messageInput.disabled = false;
            sendButton.disabled = false;
            messageInput.focus(); // Set focus back to input
        });
    }

    function handleUpload() {
        const file = pdfUploadInput.files[0];
        if (!file) {
            setUploadStatus('Please select a file first.', true);
            return;
        }

        setUploadStatus(`Uploading ${file.name}...`);
        addMessage(`Uploading ${file.name}...`, 'system');

        const formData = new FormData();
        formData.append('file', file);

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                // Try to parse error message from JSON response
                return response.json().then(errData => {
                    throw new Error(errData.error || `HTTP error! status: ${response.status}`);
                }).catch(() => {
                    // Fallback if response is not JSON or parsing fails
                    throw new Error(`HTTP error! status: ${response.status}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log("Upload response:", data);
            setUploadStatus(data.message || `Successfully processed ${file.name}.`, false);
            addMessage(data.message || `Processed ${file.name}. Ready for input.`, 'system');

            if (data.type === 'csv') {
                // Handle CSV upload info (maybe just display filename)
                updatePdfInfo(data.filename + " (CSV)", null); // Indicate it's a CSV
                // Clear other sections as PDF logic doesn't apply
                updateFilledFields(null);
                clearDownloads();
            } else {
                // Handle PDF upload info
                updatePdfInfo(data.filename, data.fields);
                // Clear previous results when a new PDF is uploaded
                updateFilledFields(null);
                clearDownloads();
            }
        })
        .catch(error => {
            console.error('Upload error:', error);
            const errorMessage = `Upload failed: ${error.message}`;
            setUploadStatus(errorMessage, true);
            addMessage(errorMessage, 'system');
            updatePdfInfo(null, null); // Clear PDF info on error
        })
        .finally(() => {
             pdfUploadInput.value = ''; // Clear file input regardless of success/failure
        });
    }

    // --- Initial Setup ---
    updatePdfInfo(null, null);
    updateFilledFields(null);
    clearDownloads();

});