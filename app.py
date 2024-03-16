from flask import Flask, request, jsonify
from exa_py import Exa
from openai import OpenAI
import os

app = Flask(__name__)
exa = Exa(os.environ["EXA_API_KEY"])
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
autistic_keywords = ['autism','autistic']

def generate_augmented_questions(questions):
    augmented_questions = []
    for question in questions:
        for keyword in autistic_keywords:
            if keyword not in question:
                question += ' autism'
                augmented_questions.append(question)
    return augmented_questions


def get_highlights_from_exa(question):
    search_response = exa.search_and_contents(
            question,
            num_results=10,
            use_autoprompt=True,
            highlights={"num_sentences": 5, "query": question, "highlights_per_url": 1},
            )
    highlight_parts = ['Title:' + result.title + ',' + 'Url: ' + result.url + 'Content: ' + result.highlights[0]  if result.highlights else '' for result in search_response.results]
    return '| '.join(highlight_parts)

def get_summary_from_openai(system_content, user_content):
    completion = client.chat.completions.create(
    model="gpt-3.5-turbo-0125",
    messages=[
            {"role": "system", "content" : system_content },
            {"role": "user", "content": user_content}
    ]
    )
    return completion.choices[0].message.content


@app.route('/augment-and-summarize', methods=['POST'])
def augment_and_summarize():
    data = request.get_json()
    if 'questions' not in data or not isinstance(data['questions'], list):
        return jsonify({'error': 'Invalid input. Expected "questions" as a list of strings.'}), 400
    augmented_questions = generate_augmented_questions(data['questions'])   
    highlights_list = []
    summary = ''

    try: 
        for question in augmented_questions:
           highlights_list.append(get_highlights_from_exa(question))

        system_content = "You are a blog writer. Write an article using based on below content not exceeding 200 words including citations. The article should be based on the keywords in the following questions " + ', '.join(augmented_questions)
        user_content = ', '.join(highlights_list)
        summary = get_summary_from_openai(system_content, user_content)
    except:
        return jsonify({'error': 'Error in retriving summary. please try again'}), 400
        
    # Return the summarized string
    return jsonify({'summary': summary})  # Return first 200 characters

if __name__ == '__main__':
    app.run(debug=True)
