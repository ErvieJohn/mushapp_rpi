import serial
import time
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import db


# Initialize Firebase Admin SDK with your service account credentials
cred = credentials.Certificate("/home/admin/Desktop/main/key.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://mushapp-c0311-default-rtdb.firebaseio.com/'
})
jsonData = {'temperature': -170, 'humidity': 9999.7, 'waterLevel': 0, 'co2ppm': 226}
print("TEST SENDING DATA: ", jsonData)
# Reference to the specific path in the Firebase Realtime Database
ref = db.reference('/')

ref.update({"temp":jsonData["temperature"]})
ref.update({"humid":jsonData["humidity"]})
ref.update({"water":jsonData["waterLevel"]})
ref.update({"co2":jsonData["co2ppm"]})

print("TEST SENT DATA")
