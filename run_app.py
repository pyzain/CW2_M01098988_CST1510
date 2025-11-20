# run_app.py
import sys
import os
import subprocess

# Add the project root directory to sys.path so 'app' can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    # Run Streamlit for your main_app.py
    subprocess.call(["streamlit", "run", "main_app.py"])
