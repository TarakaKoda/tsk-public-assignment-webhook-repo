from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

client = MongoClient("mongodb+srv://webhook:sunrisers@cluster0.zvfiydd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0/")
db = client.webhookdb
collection = db.events

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
    data = request.json
    event_type = request.headers.get('X-GitHub-Event')
    if event_type == "push":
        handle_push_event(data)
    elif event_type == "pull_request":
        if data["action"] == "closed" and data["pull_request"]["merged"]:
            handle_merge_event(data)
        else:
            handle_pull_request_event(data)
    return "OK"

def handle_push_event(data):
    event = Event(
        author=data["pusher"]["name"],
        event_type="push",
        to_branch=data["ref"].split('/')[-1]
    )
    collection.insert_one(event.to_dict())

def handle_pull_request_event(data):
    event = Event(
        author=data["sender"]["login"],
        event_type="pull_request",
        from_branch=data["pull_request"]["head"]["ref"],
        to_branch=data["pull_request"]["base"]["ref"]
    )
    collection.insert_one(event.to_dict())

def handle_merge_event(data):
    event = Event(
        author=data["sender"]["login"],
        event_type="merge",
        from_branch=data["pull_request"]["head"]["ref"],
        to_branch=data["pull_request"]["base"]["ref"]
    )
    collection.insert_one(event.to_dict())

@app.route('/events', methods=['GET'])
def get_events():
    events = list(collection.find({}, {'_id': 0}))
    return jsonify(events)

if __name__ == "__main__":
    app.run(port=5000)
