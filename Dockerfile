
 FROM  python:3.10-slim

WORKDIR /app

# Install required Python packages
RUN pip install pymupdf

# Copy the processing script
COPY . /app

# Run the script
CMD ["python", "process_pdfs.py"]