import pandas as pd
import json
import requests
import os
from flask import Flask, request, Response

# CONSTANT
TOKEN = '8001603130:AAF0GtliBE0rtx9Kwxd4JdO6Uo0mlb-UQJQ'

# INFO BOT
#https://api.telegram.org/bot8001603130:AAF0GtliBE0rtx9Kwxd4JdO6Uo0mlb-UQJQ/getMe

# GET UPDATE
#https://api.telegram.org/bot8001603130:AAF0GtliBE0rtx9Kwxd4JdO6Uo0mlb-UQJQ/getUpdates

# WEB HOOK
#https://api.telegram.org/bot8001603130:AAF0GtliBE0rtx9Kwxd4JdO6Uo0mlb-UQJQ/setWebhook?url=https://stephenie-confineable-overfrankly.ngrok-free.dev

# SEND MESSAGE
#https://api.telegram.org/bot8001603130:AAF0GtliBE0rtx9Kwxd4JdO6Uo0mlb-UQJQ/sendMessage?chat_id=8084855941&text=Hi Pedro


def send_message(chat_id, text):
    """Envia uma mensagem de volta ao chat do Telegram."""
    url = 'https://api.telegram.org/bot{}/sendMessage'.format(TOKEN)
    payload = {'chat_id': chat_id, 'text': text}
    
    r = requests.post(url, json=payload)
    print(f'Status Code do SendMessage: {r.status_code}')
    return None

def load_dataset( store_id ):
# loading test dataset
    df10 = pd.read_csv( 'test.csv' )
    df_store_raw = pd.read_csv('store.csv')

    # merge test dataset + store
    df_test = pd.merge( df10, df_store_raw, how='left', on='Store' )

    # choose store for prediction
    df_test = df_test[df_test['Store'] == store_id]

    if not df_test.empty:

        # remove closed days
        df_test = df_test[df_test['Open'] != 0]
        df_test = df_test[~df_test['Open'].isnull()]
        df_test = df_test.drop( 'Id', axis=1 )

        # convert Dataframe to json
        data = json.dumps( df_test.to_dict( orient='records' ) )

    else:
        data = 'error'

    return data

def predict( data ):
    # API Call
    url = 'https://rossmann-app-y09g.onrender.com/rossmann/predict'
    header = {'Content-type': 'application/json' }
    data = data
    r = requests.post( url, data=data, headers=header )
    print( 'Status Code {}'.format( r.status_code ) )

    d1 = pd.DataFrame( r.json(), columns=r.json()[0].keys() )

    return d1


def parse_message(message):
    chat_id = message['message']['chat']['id']
    store_id = message['message']['text']

    store_id = store_id.replace('/', '')

    try:
        store_id = int(store_id)
    except ValueError:
        store_id = 'error'

    return chat_id, store_id

# API Initialize
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])

def index():
    if request.method == 'POST':
        message = request.get_json()
        chat_id, store_id = parse_message(message)

        if store_id != 'error':
            #loading data
            data = load_dataset(store_id)

            if data != 'error':

                # prediction
                d1 = predict(data)

                #calculation
                d2 = d1[['store', 'prediction']].groupby( 'store' ).sum().reset_index()

                #send message
                msg = 'Store Number {} will sell R${:,.2f} in the next 6 weeks'.format(d2['store'].values[0], d2['prediction'].values[0] ) 

                send_message(chat_id, msg)
                return Response('Ok', status=200)

            else:
                send_message(chat_id, "store not avaliable")
                return Response("OK", status=200)
        else:
            send_message(chat_id, "store_id is wrong")
            return Response("OK", status=200)
    else:
        return '<h1> ROSSMANN TELEGRAM BOT </h1>'



if __name__=='__main__':
    port = os.environ.get('PORT', 5000)
    app.run(host='0.0.0.0', port=port)