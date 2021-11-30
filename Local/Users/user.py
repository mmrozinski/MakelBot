import json

# User class, responsible for managing users and contacting the user DB
class User:
    id = None
    balance = None

    def __init__(self, id):
        self.id = id

    def __init__(self, id, balance):
        self.id = id
        self.balance = balance

    # Saves the user's data in DB
    def save(self):
        user_db = open("Local/Users/userDB.json", "r")
        db_json = json.load(user_db)
        user_db.close()
        user_db = open("Local/Users/userDB.json", "w")
        db_json.append({"id" : self.id, "balance" : self.balance})
        json.dump(db_json, user_db)
        user_db.close()
    
    # Checks if user is present in DB
    def isPresent(self):
        return
    
    # Pulls the user's data from the DB
    def getData(self):
        return

    # Creates a new user
    def _create(self):
        return
    
    # Saves the user into the user DB (creates or updates)
    def _update(self):
        return