import openai
from api import api_key

def answer(max_tokens):
    question = input('What is your question?\n') 
    answer = openai.ChatCompletion.create(            
            api_key=api_key,
            model="gpt-3.5-turbo",
            max_tokens=max_tokens,
            messages=[        
                    {"role": "user", "content": question}
                ]
            )['choices'][0]['message']['content']
    sentences = answer.split('.')
    print('.'.join(sentences[:-1])+'.')

answer(50)