# Migration Guide

This document provides guidance on how to migrate from the old PhotoDisarm structure to the new refactored structure.

## Overview of Changes

The project has been completely refactored to follow SOLID principles:

1. **Single Responsibility Principle**: Each class has only one reason to change
2. **Open/Closed Principle**: Components are open for extension but closed for modification
3. **Liskov Substitution Principle**: Types can be substituted with subtypes
4. **Interface Segregation Principle**: Specific interfaces are better than one general-purpose interface
5. **Dependency Inversion Principle**: High-level modules don't depend on low-level modules

## Directory Structure Changes

Old structure:
```
PhotoDisarm/
├── launcher.py
├── photodisarm/
│   ├── __init__.py
│   ├── blurry.py
│   ├── canvas.py
│   ├── dub.py
│   └── util.py
```

New structure:
```
PhotoDisarm/
├── launcher_new.py        # Simple entry point
├── src/                   # Source code root
│   ├── main.py            # Application entry point
│   └── photodisarm/       # Main package
│       ├── __init__.py
│       ├── __main__.py
│       ├── core/          # Core business logic
│       │   └── image_viewer.py
│       ├── i18n/          # Internationalization
│       │   └── localization.py
│       ├── processing/    # Image processing
│       │   ├── background_processor.py
│       │   ├── duplicates.py
│       │   └── image_processor.py
│       ├── ui/            # User interface
│       │   └── app.py
│       └── utils/         # Utilities
│           ├── drawing.py
│           └── file_utils.py
```

## Migration Steps

1. **Backup the old code**
   ```
   mkdir backup
   cp -r photodisarm backup/
   cp launcher.py backup/
   ```

2. **Rename the new files**
   ```
   mv launcher_new.py launcher.py
   mv pyproject_new.toml pyproject.toml
   mv README_new.md README.md
   ```

3. **Update dependencies**
   ```
   # Using pip
   pip install -r requirements.txt
   
   # Or using Poetry
   poetry install
   ```

4. **Run the application**
   ```
   python launcher.py
   ```
   
   or
   
   ```
   python src/main.py
   ```
   
   or using the batch file:
   
   ```
   run_photodisarm.bat
   ```

## Key Benefits of the New Structure

1. **Maintainability**: Code is easier to understand and modify
2. **Extensibility**: New features can be added without changing existing code
3. **Testability**: Components can be tested in isolation
4. **Readability**: Code organization makes the system architecture clearer
5. **Reusability**: Components can be reused in other projects

## Migration Verification

After migration, ensure that all features are working correctly:

- Image loading and viewing
- Forward/backward navigation
- Saving and deleting images
- Duplicate detection
- Sorting by date
- Language switching
- Background processing of images

If any issues are encountered, please refer to the error messages or logs for troubleshooting.
