# OCDB — Cognitive Database Framework

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Version-v1.1.2-orange)

OCDB (Orbynt Cognitive Database) is a lightweight, modular framework that combines
**🧠 Memory**, **🔍 Vector Search**, **🕸 Graph Reasoning**, and **🛡 Safety Scanning** into a single Python package.

Designed for:

- AI agents
- Chatbots
- Automation systems
- Reasoning pipelines
- Personal assistants
- Any system that needs context, memory, search, and safety  

This is the **local developer** version for PyPI.
A fully hosted **OCDB Cloud Platform** will launch separately.

---

## ✨ Features


### 🧠 1. Memory Engine
Store and retrieve structured memory using a simple API.

```python
from orbmem.core.ocdb import OCDB

ocdb = OCDB()
ocdb.memory_set("name", {"value": "Abhishek"})
print(ocdb.memory_get("name"))
```

---


### 🔍 2. Vector Search (FAISS local engine)
Semantic search powered by FAISS.

```python
ocdb.vector_engine.add_text("hello world", {"id": "1"})
results = ocdb.vector_search("hello", k=3)
```

---

### 🕸 3. Graph Engine (NetworkX)
Build reasoning trees or node-based logic.

```python
ocdb.graph_add("root", "Start")
ocdb.graph_add("child", "Next", parent="root")
```

---

### 🛡 4. Safety Engine
Simple text-safety scanning with MongoDB + time-series tracking.

```python
events = ocdb.safety_scan("This is a sample text")
```

---

### 📦 Installation

```nginx
pip install orbmem
```

---

### 📁 Project Structure
```makefile
ocdb/
 ├── core/        # Config, auth, high-level OCDB interface
 ├── engines/     # Memory, vector, graph, safety engines
 ├── models/      # Memory & safety models
 ├── utils/       # Helpers, exceptions, logging
 └── db/          # Database connectors (Mongo, Neo4j, Postgres, Redis)
```

---

### 🚀 Quickstart Example

```python
from orbmem.core.ocdb import OCDB

ocdb = OCDB()

# Memory
ocdb.memory_set("demo", {"text": "Hello OCDB"})
print(ocdb.memory_get("demo"))

# Vector
print(ocdb.vector_search("Abhishek"))

# Graph
ocdb.graph_add("n1", "Start")
ocdb.graph_add("n2", "Next", parent="n1")

# Safety
print(ocdb.safety_scan("Harmless text"))
```

### Install dependencies:

```bash
pip install -r requirements.txt
```

From source:

```bash
git clone https://github.com/abhis-byte/orbynt-database-OrbMem.git
cd orbmem
pip install .
pip install -r requirements.txt
```

---

### 🚀 Basic Usage

```python
from orbmem.core.ocdb import OCDB 
db = OCDB()
```
This initializes:

- SQLite memory backend
- NetworkX graph backend
- SQLite safety backend (unless MONGO_URL is set)
- FAISS fallback vector backend
- Time-series safety tracking

---

### 🧠 Memory Engine (SQLite)
Store memory:

```python
db.memory_set("user", {"name": "Abhishek"})
``` 

Retrieve memory:

```python
print(db.memory_get("user"))
```

List keys:

```python
print(db.memory_keys())
```

The memory engine is SQLite-based and works everywhere without configuration.

---

### 🔗 Graph Engine (NetworkX fallback)
Add graph nodes:

```python
db.graph_add("root", "This is the root node") 
db.graph_add("child", "This is a child node", parent="root")
```

Get relationship path:

```python
print(db.graph_path("root", "child"))
``` 

Dump full graph:

```python
print(db.graph_dump())
```

The graph engine automatically uses NetworkX unless Neo4j configuration is provided.

---

### 🔍 Vector Engine (FAISS Fallback)
Version 1 uses a lightweight FAISS fallback for simple vector search examples.

Future versions (v2) will include:

- Real embeddings (SentenceTransformers)
- Qdrant/FAISS hybrid vector search
- Cloud embedding cache
- High-performance ANN indexing

Current example:

```python
results = db.vector_search("hello world", k=3)
print(results)
```
---

### 🛡 Safety Engine (SQLite / Mongo)
The safety engine detects unsafe text patterns and records violations.

Scan text:

```python
db.safety_scan("This text contains harmful intent.")
print(events)
```

Safety results contain:

- text
- tag
- severity
- correction
- details
- timestamp

Example output:

```json
[
  {
    "text": "This text contains harmful intent.",
    "tag": "violence",
    "severity": 0.6,
    "correction": "Avoid harmful or violent expressions.",
    "details": {"pattern": ""},
    "timestamp": "2025-01-01T12:00:00Z"
  }
]
```

Backend selection:

- If MONGO_URL is set → MongoSafetyBackend
- Else → SQLiteSafetyBackend (portable)

---

### 📘 Example Code (Quick Demo)

```python
from orbmem.core.ocdb import OCDB

db = OCDB()

# Memory
db.memory_set("user", {"name": "Abhishek"})
print(db.memory_get("user"))

# Vector search
print(db.vector_search("hello", k=3))

# Graph
db.graph_add("root", "Root node")
db.graph_add("child", "Child node", parent="root")
print(db.graph_path("root", "child"))
print(db.graph_dump())

# Safety engine
db.safety_scan("This may be violent content")
```

---

### 📌 Notes

- Designed for local usage (v1)
- Cloud support coming in v2
- SQLite-only mode works in all environments:
  - Kaggle
  - Jupyter
  - Colab
  - VSCode
- Windows/macOS/Linux
- No environment variables required for v1

---

### 💙 ORBMEM Cloud (Coming in v2)

- Real SentenceTransformer embeddings
- Qdrant / FAISS hybrid vector engine
- Neo4j cloud graph reasoning
- MongoDB safety event storage
- Postgres memory engine
- API keys
- Developer dashboard
- Remote sync

 Stay tuned.

---

### 📝 License
This project is released under the *MIT License*.                       
See the `LICENSE` file for full terms.

---

### 👨‍💻 Author
**Tetala Lakshmi Abhishek Reddy**            
Creator of OCDB                   
📧Email: `abhishek.orbynt@gmail.com`

---

### ⭐ Support OCDB
If you like this project, please star the repository and share it!  
The OCDB Cloud Dashboard + Hosted API is coming soon… 🚀
