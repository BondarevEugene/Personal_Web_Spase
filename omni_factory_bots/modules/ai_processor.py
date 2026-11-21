import ollama


async def run(context, config):
    user_text = context['message'].text
    # Обращаемся к вашей локальной нейронке
    response = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': user_text}])
    await context['message'].answer(response['message']['content'])
    return {"status": "ai_responded"}
