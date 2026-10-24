from app.llm import embed

vec = embed(["hello"])
print("Embedding length:", len(vec[0]))