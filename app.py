from flask import Flask, request, jsonify
import awsgi
from flask_cors import CORS
from pymongo import MongoClient, errors
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  # Enable CORS

# MongoDB connection
try:
    client = MongoClient("mongodb+srv://webhookdb:sunrisers@cluster0.zvfiydd.mongodb.net/webhookdb?retryWrites=true&w=majority&appName=Cluster0")
    db = client.webhookdb  # Access the 'webhookdb' database
    collection = db.events  # Access the 'events' collection
    print("Connected to MongoDB")
except errors.ConnectionError as ce:
    print(f"Connection error: {ce}")
except errors.ConfigurationError as cfg:
    print(f"Configuration error: {cfg}")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

class Event:
    def __init__(self, author, event_type, from_branch=None, to_branch=None, timestamp=None):
        self.author = author
        self.event_type = event_type
        self.from_branch = from_branch
        self.to_branch = to_branch
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self):
        return {
            "author": self.author,
            "event_type": self.event_type,
            "from_branch": self.from_branch,
            "to_branch": self.to_branch,
            "timestamp": self.timestamp
        }

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        event_type = request.headers.get('X-GitHub-Event')
        if event_type == "push":
            handle_push_event(data)
        elif event_type == "pull_request":
            if data["action"] == "closed" and data["pull_request"]["merged"]:
                handle_merge_event(data)
            else:
                handle_pull_request_event(data)
        return "OK", 200
    except Exception as e:
        print(f"Error in webhook processing: {e}")
        return "Internal Server Error", 500

def handle_push_event(data):
    try:
        event = Event(
            author=data["pusher"]["name"],
            event_type="push",
            to_branch=data["ref"].split('/')[-1]
        )
        collection.insert_one(event.to_dict())
        print("Push event handled successfully")
    except Exception as e:
        print(f"Error handling push event: {e}")

def handle_pull_request_event(data):
    try:
        event = Event(
            author=data["sender"]["login"],
            event_type="pull_request",
            from_branch=data["pull_request"]["head"]["ref"],
            to_branch=data["pull_request"]["base"]["ref"]
        )
        collection.insert_one(event.to_dict())
        print("Pull request event handled successfully")
    except Exception as e:
        print(f"Error handling pull request event: {e}")

def handle_merge_event(data):
    try:
        event = Event(
            author=data["sender"]["login"],
            event_type="merge",
            from_branch=data["pull_request"]["head"]["ref"],
            to_branch=data["pull_request"]["base"]["ref"]
        )
        collection.insert_one(event.to_dict())
        print("Merge event handled successfully")
    except Exception as e:
        print(f"Error handling merge event: {e}")

@app.route('/events', methods=['GET'])
def get_events():
    try: 
        events = list(collection.find({}, {'_id': 0}))
        return jsonify(events), 200
    except Exception as e:
        print(f"Error fetching events: {e}")
        return jsonify({"error": "Error fetching events"}), 500
    
def lambda_handler(event, context):
    return awsgi.response(app, event, context, base64_content_types={"image/png"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

