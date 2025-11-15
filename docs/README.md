# CW2 – Multi-Domain Intelligence Platform

## Overview
This is a **beginner-friendly Streamlit project** that unifies three domain dashboards in one platform:

- 🛡️ **Cybersecurity** — analyze and visualize incident trends  
- 🖥️ **IT Operations** — track and visualize service tickets  
- 📊 **Data Science** — explore datasets and generate usage insights  

The app includes secure login using **bcrypt**, optional local SQLite database, and interactive visualizations.

---

### 1. Create a Virtual Environment
```bash
python -m venv .venv
```

### 2. Activate the Environment
- **Windows (PowerShell)**:
```bash
.venv\Scripts\Activate.ps1
```
- **macOS / Linux**:
```bash
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize Database & Sample Data
```bash
python migration_script.py
```
This creates `DATA/intelligence_platform.db` (optional) and sample user/data files.

### 5. Run the App
- **Option A (recommended)**:
```bash
python run_app.py
```
- **Option B (direct Streamlit launch)**:
```bash
streamlit run app/main_app.py
```

### Demo Login
- **Username:** demo  
- **Password:** demo123  

Or register a new account from the **Register** tab on the login page. Credentials are saved in `DATA/users.txt`.

---

## Project Structure
```
CW2_M0123456_CST1510/
├─ app/
│  ├─ main_app.py               # Streamlit orchestrator
│  ├─ run_all.py / run_app.py   # Optional launcher
│  ├─ common/
│  │  └─ auth_cli.py            # Handles password hashing & verification
│  └─ pages/
│     ├─ Login.py
│     ├─ Dashboard_Cyber.py
│     ├─ Dashboard_IT.py
│     └─ Dashboard_Data.py
├─ DATA/
│  ├─ users.txt                 # Stores username,hashed_password
│  ├─ cyber_incidents.csv
│  ├─ it_tickets.csv
│  └─ datasets_metadata.csv
├─ migration_script.py
├─ requirements.txt
└─ README.md
```

---

## How Login Works
1. Passwords are hashed with **bcrypt** and saved in `DATA/users.txt`.  
2. Streamlit stores the login session in `st.session_state`.  
3. Once logged in, you can access all dashboards via the sidebar.

---

## Dashboards Overview
- **Cybersecurity:** Shows incident trends and status counts.  
- **IT Operations:** Visualizes tickets by category, status, and priority.  
- **Data Science:** Summarizes datasets, shows missing values, and visualizes data distributions.

---

## Common Issues & Fixes
- **Module import errors (`No module named 'app'`)**:  
  Run from project root or use `python run_app.py`.
- **Registration not saving**:  
  Ensure `DATA/` exists and has write permission; run `migration_script.py`.
- **Streamlit rerun errors**:  
  Upgrade Streamlit: `pip install --upgrade streamlit`.

---

## Author
**Name:** Zain  
**Course:** CST1510  

### Recommended Run Command:
```bash
python run_app.py
```
Alternative:
```bash
streamlit run app/main_app.py
```
