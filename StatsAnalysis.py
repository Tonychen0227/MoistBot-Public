from FirebaseService import FirebaseService

service = FirebaseService()
database = service.firebase.database()

statistics = database.child("statistics").child("poll_winners").get()

total = {}

for pyre in statistics.pyres:
    for key in pyre.val():
        if key in total:
            total[key] = total[key] + pyre.val()[key]
        else:
            total[key] = pyre.val()[key]

print(sorted(total.items(), key=lambda x: x[1]))

statistics = database.child("statistics").child("users").get()

count = 0

for pyre in statistics.pyres:
    print(pyre.val())
    for key in pyre.val():
        count += pyre.val()[key]

print(count)