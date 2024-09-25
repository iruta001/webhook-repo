from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# Set up MongoDB connection
client = MongoClient('mongodb://localhost:27017')
db = client['webhook_db']
events = db['events']

@app.route('/webhook', methods=['POST'])
def github_webhook():
    payload = request.json
    event_type = request.headers.get('X-GitHub-Event')
    event_data = {}

    # Handle "Push" event
    if event_type == "push":
        event_data = {
            "author": payload['pusher']['name'],
            "to_branch": payload['ref'].split('/')[-1],
            "event_type": "push",
            "timestamp": datetime.utcnow()
        }

    # Handle "Pull Request" event
    elif event_type == "pull_request":
        pr_action = payload['action']
        if pr_action == "opened":
            event_data = {
                "author": payload['pull_request']['user']['login'],
                "from_branch": payload['pull_request']['head']['ref'],
                "to_branch": payload['pull_request']['base']['ref'],
                "event_type": "pull_request",
                "timestamp": datetime.utcnow()
            }

    # Handle "Merge" event (optional brownie points)
    elif event_type == "pull_request" and payload['pull_request']['merged']:
        event_data = {
            "author": payload['pull_request']['user']['login'],
            "from_branch": payload['pull_request']['head']['ref'],
            "to_branch": payload['pull_request']['base']['ref'],
            "event_type": "merge",
            "timestamp": datetime.utcnow()
        }

    # Store event data in MongoDB
    if event_data:
        events.insert_one(event_data)

    return jsonify({"message": "Event received!"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
