from flask import Flask, request, redirect, url_for, render_template
from flask_socketio import SocketIO, emit
import pandas as pd
import os
import threading
import billinfo

app = Flask(__name__, static_folder='static')
socketio = SocketIO(app)

# Load congressmen names
names_df = pd.read_csv('congressmen_names.csv')
congressmen_names = names_df['full_name'].tolist()

def update_website(congress, bill_type, bill_number, congressman=None):
    committees, cosponsors, subjects, text_bert, titles_bert, summaries_bert = billinfo.get_bill_info(congress, bill_type.lower(), bill_number)
    with open('congressman.html', 'r', encoding='utf-8') as file:
        content = file.read()
    soup = BeautifulSoup(content, 'lxml')
    h1_tag = soup.find('h1')
    if h1_tag:
        h1_tag.string = 'Prediction:'
    cards = soup.find_all('div', class_='card')
    iteration = 1
    percentage = round((iteration / len(cards)) * 100, 2)
    corrupt = pd.DataFrame(columns=['name'])
    bill_df = pd.read_json('bills_categorical.json')

    files = os.listdir('congressman_votes_data')
    
    # Filter files if a specific congressman is selected
    if congressman and congressman != 'All':
        files = [f for f in files if congressman.replace(' ', '_') in f]

    for card in cards:
        bioguide_id = card.find('img')['src'][38:45]
        file_name = None
        for file in files:
            if not file.endswith('.csv'):
                continue
            if bioguide_id in file:
                file_name = file
                break

        if file_name:
            try:
                new_bill = billinfo.get_congressman_specific_encoding(pd.read_csv('congressman_votes_data/' + file_name), committees, cosponsors, subjects, text_bert, titles_bert, summaries_bert, bill_df=bill_df)
                model_location = 'DistilBERT/' + file_name.strip('.csv') + '.keras'
                prediction_percentage = billinfo.predict(model_location, new_bill) * 100
            except Exception as e:
                corrupt.loc[len(corrupt)] = file_name
                print(f"Error processing {file_name}: {e}")
                prediction_percentage = 0.5

            details = card.find('div', class_='details')
            vote = details.find_all('p', class_='vote')[0]
            yea_prob = details.find_all('p', class_='vote')[1]
            nay_prob = details.find_all('p', class_='vote')[2]
            stats = details.find_all('p', class_='vote')[3]

            vote.string = f"Vote: {'Yea' if prediction_percentage <= 0.5 else 'Nay'}"
            yea_prob.string = f"Yea Probability: {round(1 - prediction_percentage, 2)}%"
            nay_prob.string = f"Nay Probability: {round(prediction_percentage, 2)}%"
            stats.string = "Accuracy: None"
            socketio.emit('update_progress', {'progress': percentage})
            iteration += 1
            percentage = round((iteration / len(cards)) * 100, 2)

    corrupt.to_csv('corruptv2.csv')

    with open('templates/congressman.html', 'w', encoding='utf-8') as file:
        file.write(str(soup))

@app.after_request
def add_ngrok_header(response):
    response.headers['ngrok-skip-browser-warning'] = 'true'
    return response

@app.route('/')
def index():
    return render_template('index.html', congressmen=congressmen_names)

@app.route('/predict', methods=['POST'])
def predict():
    congress = request.form['congress']
    billType = request.form['billType']
    billNumber = request.form['billNumber']
    congressman = request.form['congressman'] if 'congressman' in request.form else None

    threading.Thread(target=background_task, args=(congress, billType, billNumber, congressman)).start()
    return redirect(url_for('loading', congress=congress, billType=billType, billNumber=billNumber))

@app.route('/loading')
def loading():
    return render_template('loading.html')

@app.route('/congressman')
def congressman():
    return render_template('congressman.html')

def background_task(congress, billType, billNumber, congressman):
    update_website(congress, billType, billNumber, congressman)
    socketio.emit('redirect', {'url': 'congressman'})

if __name__ == '__main__':
    socketio.run(app, debug=True)
