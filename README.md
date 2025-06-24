# PhotoDisarm

PhotoDisarm is a tool for managing and processing photos, with special support for handling RAW image formats like NEF.

## Features

- Sort and organize images by date
- Detect and handle duplicate images
- Process and view images, including large RAW files
- Background processing for responsive UI
- Multilingual support (English and Danish)

## Installation

### Using Poetry (recommended)

```bash
# Install dependencies
poetry install

# Run the application
poetry run python src/main.py
```

### Using pip

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```

## Project Structure

The project is organized according to SOLID principles:

```
photodisarm/
├── core/          # Core business logic
├── i18n/          # Internationalization
├── processing/    # Image processing modules
├── ui/            # User interface
└── utils/         # Utility functions
```

## Usage

1. Select input directory containing images
2. Choose output directory for organized files
3. Configure processing options
4. Click "Start Processing"
5. Use keyboard shortcuts to manage images:
   - Space: Save the current image
   - Backspace: Delete the current image
   - Left Arrow: Go back to the previous image
   - Any other key: Skip to the next image

## Building a Standalone Executable

To build a standalone executable:

```bash
# Install PyInstaller
pip install pyinstaller

# Build the executable
pyinstaller --onefile --windowed --name PhotoDisarm src/main.py
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
