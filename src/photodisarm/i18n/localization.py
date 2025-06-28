"""
Localization module for PhotoDisarm

Provides language support for the application.
"""
from typing import Dict, Any


class LocalizationService:
    """Service for handling application localization"""
    
    # Language codes
    ENGLISH = "en"
    DANISH = "da"
    
    # Default language dictionaries
    _languages: Dict[str, Dict[str, Any]] = {
        ENGLISH: {
            "window_title": "Image Processing Interface",
            "input_dir": "Input Directory",
            "output_dir": "Output Directory",
            "browse": "Browse",
            "chunk_size": "Chunk Size",
            "max_width": "Max Width",
            "max_height": "Max Height",
            "delete_duplicates": "Delete Duplicates",
            "search_recursively": "Search Recursively",
            "start_processing": "Start Processing",
            "switch_lang": "Skift til dansk",  
            "error": "Error",
            "invalid_dir": "Invalid directory path!",
            "done": "Done!",
            "all_processed": "All images processed!",
            "image_window": "Image",
            "loading_chunk": "Loading chunk",
            "images": "images",
            "sorted_by_date": "Sorted by date",
            "processing_image": "Processing image",
            "no_date": "*No Date Found*",
            "keybindings": "Space: Save | Backspace: Delete | ← : Back | → : Forward | Any key: Skip",
            "use_cache": "Use Cache (Faster)",
            "image_quality": "Image Quality:",
            "quality_low": "Low (Fast)",
            "quality_normal": "Normal",
            "quality_high": "High (Best)",
            "directories_settings": "Directory Settings",
            "processing_parameters": "Processing Parameters",
            "keybind_settings": "Key Bindings",
            "save_keybind": "Save Image Key:",
            "delete_keybind": "Delete Image Key:",
            "keybind_help": "(Click and press key)",
            "options_settings": "Options",
            "quality_settings": "Image Quality Settings",
            "preloading": "Preloading next images in background...",
            "loaded_from_cache": "Image loaded from preload cache",            "status_saved": "Saved",
            "status_deleted": "Deleted",
            "status_skipped": "",
            "status_history": "History: {count}/10",
            "sort_by_date": "Sort images by date before processing"
        },
        DANISH: {
            "window_title": "Billedbehandlingsværktøj",
            "input_dir": "Inputmappe",
            "output_dir": "Outputmappe",
            "browse": "Gennemse",
            "chunk_size": "Gruppestørrelse",
            "max_width": "Maks. bredde",
            "max_height": "Maks. højde",
            "delete_duplicates": "Slet dubletter",
            "search_recursively": "Søg rekursivt",
            "start_processing": "Start behandling",
            "switch_lang": "Switch to English",  
            "error": "Fejl",
            "invalid_dir": "Ugyldig mappesti!",
            "done": "Færdig!",
            "all_processed": "Alle billeder er behandlet!",
            "image_window": "Billede",
            "loading_chunk": "Indlæser gruppe",
            "images": "billeder",
            "sorted_by_date": "Sorteret efter dato",
            "processing_image": "Behandler billede",
            "no_date": "*Ingen dato fundet*",
            "keybindings": "Mellemrum: Gem | Backspace: Slet | ← : Tilbage | → : Frem | Enhver tast: Spring over",
            "use_cache": "Brug cache (Hurtigere)",
            "image_quality": "Billedkvalitet:",
            "quality_low": "Lav (Hurtig)",
            "quality_normal": "Normal",
            "quality_high": "Høj (Bedst)",
            "directories_settings": "Mappeindstillinger",
            "processing_parameters": "Behandlingsparametre", 
            "keybind_settings": "Genvejstaster",
            "save_keybind": "Gem billede tast:",
            "delete_keybind": "Slet billede tast:",
            "keybind_help": "(Klik og tryk tast)",
            "options_settings": "Indstillinger",
            "quality_settings": "Billedkvalitetsindstillinger",
            "preloading": "Forudindlæser næste billeder i baggrunden...",
            "loaded_from_cache": "Billede indlæst fra forudindlæsningscache",            "status_saved": "Gemt",
            "status_deleted": "Slettet",
            "status_skipped": "",
            "status_history": "Historik: {count}/10",
            "sort_by_date": "Sortér billeder efter dato før behandling"
        }
    }
    
    # Duplicate detection translations
    _duplicate_texts = {
        ENGLISH: {
            "title": "Processing Duplicates",
            "checking": "Checking & moving duplicates...",
            "scanning": "Scanning for images...",
            "processing": "Processing images...",
            "processing_chunk": "Processing chunk {chunk_num}...",
            "elapsed_time": "Elapsed Time: {seconds}s",
            "processed": "Processed: {count}",
            "duplicates": "Duplicates: {count}",
            "complete": "Processing Complete",
            "complete_message": "{count} duplicates found and moved to {directory}"
        },
        DANISH: {
            "title": "Behandler dubletter",
            "checking": "Kontrollerer og flytter dubletter...",
            "scanning": "Scanner efter billeder...",
            "processing": "Behandler billeder...",
            "processing_chunk": "Behandler gruppe {chunk_num}...",
            "elapsed_time": "Forløbet tid: {seconds}s",
            "processed": "Behandlet: {count}",
            "duplicates": "Dubletter: {count}",
            "complete": "Behandling fuldført",
            "complete_message": "{count} dubletter fundet og flyttet til {directory}"
        }
    }
    
    def __init__(self):
        """Initialize with default language (Danish)"""
        self._current_language_code = self.DANISH
        
    def switch_language(self) -> None:
        """Switch between English and Danish"""
        if self._current_language_code == self.ENGLISH:
            self._current_language_code = self.DANISH
        else:
            self._current_language_code = self.ENGLISH
            
    @property
    def current_language_code(self) -> str:
        """Get the current language code"""
        return self._current_language_code
    
    @property
    def current_language(self) -> Dict[str, str]:
        """Get the current language dictionary"""
        return self._languages[self._current_language_code]
    
    @property
    def current_duplicate_texts(self) -> Dict[str, str]:
        """Get the current duplicate texts dictionary"""
        return self._duplicate_texts[self._current_language_code]
    
    def get_text(self, key: str, default: str = None) -> str:
        """
        Get text for a given key in the current language
        
        Args:
            key: The dictionary key
            default: Default text if key is not found
            
        Returns:
            The localized text
        """
        return self.current_language.get(key, default or key)


# Create a global instance
localization = LocalizationService()
