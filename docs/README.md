# **📘 Multi-Domain Intelligence (MDI) Platform**

A unified Streamlit application that brings together **Cybersecurity**, **Data Science**, **IT Operations**, and an **AI Assistant** into one easy-to-use, interactive dashboard.

This platform is designed for learning, analysis, and intelligent decision-making across multiple operational domains. It includes full **user authentication**, **admin management**, **visual analytics**, and an embedded **AI reasoning engine** powered by OpenAI/HuggingFace models.

---

# **🚀 Features Overview**

### ✅ **1. Secure User Authentication**

* SHA-256 password hashing
* Login / Logout
* Role-based access (User / Admin)

### ✅ **2. Admin Panel**

* Create users
* Delete users
* Reset passwords
* Export user list as CSV

### ✅ **3. Multi-Domain Dashboards**

Each dashboard follows the same structure for consistency:

#### **🛡 Cybersecurity Dashboard**

* Incident dataset analysis
* KPI summary
* Visual trends (attack types, severity, timelines)
* AI assistant for cybersecurity guidance

#### **📊 Data Science Dashboard**

* Dataset catalog with filters
* Visualizations (histogram, bar charts, scatterplots)
* Snapshot-based AI assistant that interprets data, explains ML concepts, and guides preprocessing

#### **🛠 IT Operations Dashboard**

* IT tickets overview
* KPIs and charts
* AI assistant for troubleshooting guidance

### ✅ **4. AI Assistant (Global)**

* Full conversational interface
* Domain-aware responses
* Memory-based context snapshots
* Can answer general questions or domain-specific ones
* Configurable through `.streamlit/secrets`

### ✅ **5. Built-in SQLite Database**

* Automatic initialization on first run
* `platform.db` stores users + all domain datasets
* Clean separation using a Database Manager service

---

# **📁 Project Structure**

```
CW2_M01098988_CST1510/
├─ ai_core.py 
├─ app/
│  ├─ components/
│  ├─ models/
│  │  ├─ dataset.py 
│  │  ├─ it_ticket.py 
│  │  ├─ security_incident.py 
│  │  ├─ user.py 
│  ├─ services/
│  │  ├─ ai_assistant.py 
│  │  ├─ auth_manager.py 
│  │  ├─ database_manager.py 
├─ data/
│  ├─ cyber_incidents.csv 
│  ├─ datasets_metadata.csv 
│  ├─ it_tickets.csv 
├─ database/
│  ├─ db.py 
│  ├─ db_initializer.py 
│  ├─ platform.db 
├─ docs/
│  ├─ README.md 
├─ img/
├─ main_app.py 
├─ make_admin_script.py 
├─ pages/
│  ├─ AI_Assistant.py 
│  ├─ Cybersecurity.py 
│  ├─ Data_Science.py 
│  ├─ Home.py 
│  ├─ IT_Operations.py 
│  ├─ users_admin.py 
├─ requirements.txt 
```

---

# **⚙️ Installation & Setup**

### **1️⃣ Clone the Repository**

```bash
git clone https://github.com/your-username/mdi-platform.git
cd mdi-platform
```

### **2️⃣ Install Requirements**

```bash
pip install -r requirements.txt
```

### **3️⃣ Create `.streamlit/secrets.toml`**

This is required for the AI Assistant.

👉 **Create this folder and file:**

```
.streamlit/
   └── secrets.toml
```

👉 **Add your API key:**

```toml
OPENAI_API_KEY = "your_api_key_here"
HF_TOKEN = "optional_huggingface_token"
```

⚠️ Without this file, the AI features will not work.

### **4️⃣ Initialize Database**

Runs automatically when you launch the app.

If needed manually:

```bash
python make_admin_script.py
```

### **5️⃣ Run the App**

```bash
streamlit run main_app.py
```

---

# **🧩 How the App Works**

### **Streamlit UI (Views)**

* Located in `/pages/`
* Each page follows a modular structure (`render()` function)

### **Business Logic (Controllers)**

* Authentication
* Database operations
* AI processing
  Located in:

```
app/services/
```

### **Data Models (Models)**

Located in:

```
app/models/
```

They define:

* User
* Dataset
* SecurityIncident
* ITTicket

---

# **🤖 AI Assistant (Technical Notes)**

### Uses:

* OpenAI ChatCompletions API (default)
* HuggingFace text-generation models (fallback)

### Smart Features:

* Adds dataset snapshots (Data Science)
* Adds ticket snapshots (IT Ops)
* Adds incident summaries (Cybersecurity)
* Maintains per-page chat history
* Respects domain restrictions

---

# **👤 Admin Usage**

### Create Admin User

```bash
python make_admin_script.py
```

### Admin Privileges

* Can access **Admin Panel** from sidebar
* Manage all system users
* Reset passwords securely

---

# **🧪 Example Code Snippet (Dashboard Structure)**

Each dashboard follows the same structure:

```python
st.title("📊 Data Science")

df = load_data()

# KPIs
c1, c2, c3 = st.columns(3)
c1.metric("Datasets", len(df))

# Visuals
fig = px.histogram(df, x="rows")
st.plotly_chart(fig)

# AI Assistant
assistant = AIAssistant(role_prompt="...")
reply = assistant.ask(query, context)
st.write(reply)
```

Consistent architecture = easy extension + easy maintenance.

---

# **📌 Key Highlights**

✔ Clean modular architecture
✔ Fully role-based
✔ AI-powered insights
✔ Beginner-friendly dashboards
✔ Automatic database setup
✔ Works offline except AI calls
✔ Ready for deployment

---

# **📄 License**

This project is created for academic coursework and learning purposes.

