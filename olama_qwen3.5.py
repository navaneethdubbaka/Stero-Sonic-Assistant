import requests
import json

url = "http://localhost:11434/api/chat"

print("Qwen Streaming Chat (type 'exit' to quit)\n")

while True:
    user_input = input("You: ")

    if user_input.lower() in ["exit", "quit"]:
        print("Exiting...")
        break

    payload = {
        "model": "qwen3.5:0.8b",
        "messages": [
            {"role": "user", "content": user_input}
        ],
        "options": {
            "think": False
        }
    }

    response = requests.post(url, json=payload, stream=True)

    print("Assistant: ", end="", flush=True)

    for line in response.iter_lines():
        if line:
            data = json.loads(line)

            if "message" in data:
                token = data["message"]["content"]
                print(token, end="", flush=True)

            if data.get("done"):
                break

    print("\n")