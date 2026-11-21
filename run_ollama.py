import ollama

response = ollama.chat(
    model="llama3",
    messages=[
        {
            "role": "user",
            "content": "Напиши простой Hello World на FastAPI",
        }
    ],
)

print(response["message"]["content"])