import requests
import json
import random


class StrawpollService:
    def get_poll(self, id):
        poll = requests.get(f"https://www.strawpoll.me/api/v2/polls/{int(id)}")
        return json.loads(poll.content)

    def get_popular_option(self, id):
        poll = requests.get(f"https://www.strawpoll.me/api/v2/polls/{int(id)}")
        contents = json.loads(poll.content)

        votes = contents["votes"]
        options = contents["options"]
        max_vote = -1
        for vote in votes:
            if vote > max_vote:
                max_vote = vote

        winning_options = []

        for i in range(0, len(votes)):
            if votes[i] == max_vote:
                winning_options.append(options[i])

        return random.choice(winning_options)

    def make_poll(self, title, options):
        poll = requests.post('https://www.strawpoll.me/api/v2/polls', json={
            'title': title,
            'options': options,
            'multi': True
        }, headers={"Content-Type": "application/json"})
        return int(json.loads(poll.content)["id"])
