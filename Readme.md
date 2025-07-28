# Challenge 1a

This project provides a solution for Challenge 1a. The application is containerized using Docker for easy setup and execution.

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/get-started) installed on your system.

### Project Structure

- `input/` - Place your input files here.
- `output/` - Output files will be generated here.
- `Dockerfile` - Docker build instructions.
- `process_pdfs.py` - Python file for processing pdfs.
- `Readme.md` - Project documentation.
- `requirements.txt` - Requirements file.

## How to Run

1. **Build the Docker Image**

    Replace `mysolutionname:somerandomidentifier` with your preferred image name and tag.

    ``` docker build -t mysolutionname:somerandomidentifier ```

2. **Run the Docker Container**

    This command mounts the `input` and `output` directories and runs the solution in an isolated network.

    ``` docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none mysolutionname:somerandomidentifier ```

## Notes

- Ensure the `input` directory exist in your project root.
- The application will read from `/app/input` and write results to `/app/output`.
- The application takes uploaded PDF files as input from the `input` folder.
- After processing, it generates a JSON document for each PDF in the `output` folder.
