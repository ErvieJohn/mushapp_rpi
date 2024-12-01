import firebase_admin
from firebase_admin import credentials, db

try:
    # Path to your service account key JSON file
    service_account_key_path = '/home/admin/Desktop/main/key.json'

    # Initialize the Firebase app
    cred = credentials.Certificate(service_account_key_path)
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://mushapp-c0311-default-rtdb.firebaseio.com/'
    })
    
    print("Firebase initialized successfully!")
    
except Exception as e:
    print(f"Error initializing Firebase: {e}")

# Reference the database location you want to read from
ref = db.reference('/')  # Replace with the path to your data in the database

# Get the data
data = ref.get()

# Print the retrieved data
if data:
    print("Data retrieved from Firebase Realtime Database:")
    if(data["fan"]): print("It's true")
    else: print("its false")
else:
    print("No data found at the specified location.")
