import os
import glob
import time
import PyPDF2
import google.generativeai as genai

class ResourceManager:
    """
    Manages loading and uploading of PDF resources.
    """
    def __init__(self, resource_dir="uSucceed_resource"):
        self.resource_dir = resource_dir
        self.files = []  # List of uploaded file objects from Gemini
        self.nav_guide = ""  # Content from the NAVIGATION_control.pdf file
        self.loaded = False

    def load_resources(self):
        """
        Loads all PDF files from the resource directory, uploads them to Gemini,
        and caches the navigation guide separately.
        """
        file_paths = glob.glob(os.path.join(self.resource_dir, "*.pdf"))
        self.files = []
        for path in file_paths:
            file_obj = genai.upload_file(path, mime_type="application/pdf")
            print(f"Uploaded file '{file_obj.display_name}' as: {file_obj.uri}")
            self.files.append(file_obj)

        self.wait_for_files_active(self.files)
        self._load_navigation_guide()
        self.loaded = True

    def wait_for_files_active(self, files):
        """
        Waits until each file is processed (state ACTIVE) by Gemini.
        """
        print("Waiting for file processing...")
        for file in files:
            file_obj = genai.get_file(file.name)
            while file_obj.state.name == "PROCESSING":
                print(".", end="", flush=True)
                time.sleep(10)
                file_obj = genai.get_file(file.name)
            if file_obj.state.name != "ACTIVE":
                raise Exception(f"File {file_obj.name} failed to process")
        print("\n...all files ready\n")

    def _load_navigation_guide(self):
        """
        Reads and caches the navigation guide from NAVIGATION_control.pdf.
        """
        nav_path = os.path.join(self.resource_dir, "NAVIGATION_control.pdf")
        if os.path.exists(nav_path):
            with open(nav_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                pages = [page.extract_text() for page in reader.pages]
                self.nav_guide = "\n".join(pages)
        else:
            print("Navigation control PDF not found.")

    def get_files_for_agent(self, agent_type: str):
        """
        Returns a prioritized list of files based on the agent type.
        For example, the LocationAgent prioritizes the 'CONTEXT_Rooms_And_Tasks.pdf'.
        """
        # if agent_type == "location":
        #     prioritized = [f for f in self.files if "CONTEXT_Rooms_And_Tasks.pdf" in f.display_name]
        #     print(f"Prioritized files: {[f.display_name for f in prioritized]}")
        #     others = [f for f in self.files if "CONTEXT_Rooms_And_Tasks.pdf" not in f.display_name]
        #     return prioritized + others
        # For other agent types, return all files.
        return self.files
