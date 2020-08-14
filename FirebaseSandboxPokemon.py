from FirebaseService import *

firebase = FirebaseService()
data = firebase.firebase.database().child("pokemon_information").get().val()

keys = data.keys()

copy_dict = data.copy()
for x in keys:
    temp = data[x]
    if temp["species"] == "Ditto":
        temp["ability"] = "Imposter (H)"
    else:
        temp["ability"] = "???"
    copy_dict[x] = temp

firebase.firebase.database().child("pokemon_information").update(copy_dict)
