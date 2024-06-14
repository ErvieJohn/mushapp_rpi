import json
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import db

cred = credentials.Certificate("./key.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://mushapp-c0311-default-rtdb.firebaseio.com/'
})

ref = db.reference('/')
refTemp = db.reference('/temp')

data = "{\"temperature\":25,\"humidity\":99.1,\"waterLevel\":0}"
data = json.loads(data)

print(data)
ref.update({"temp":data["temperature"]})
# db.collection("try").add(data)
