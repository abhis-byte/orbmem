from orbmem.core.ocdb import OCDB

db = OCDB()

# Memory
db.memory_set("user", {"name": "Abhishek"})
print(db.memory_get("user"))

# Vector
print(db.vector_search("hello", k=3))

# Graph
db.graph_add("root", "This is root")
db.graph_add("child", "Child node", parent="root")
print(db.graph_path("root", "child"))

# Safety
print(db.safety_scan("I will kill you"))
