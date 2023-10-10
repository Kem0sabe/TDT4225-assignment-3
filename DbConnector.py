from pymongo import MongoClient, version


class DbConnector:
    """
    Connects to the MongoDB server on the Ubuntu virtual machine.
    Connector needs HOST, USER and PASSWORD to connect.

    Example:
    HOST = "tdt4225-00.idi.ntnu.no" // Your server IP address/domain name
    USER = "testuser" // This is the user you created and added privileges for
    PASSWORD = "test123" // The password you set for said user
    """

    def __init__(self,
                 DATABASE='test_db',
                 HOST='localhost',
                 USER=None,
                 PASSWORD=None):

        if USER and PASSWORD:
            uri = f"mongodb://{USER}:{PASSWORD}@{HOST}/{DATABASE}?authSource=admin"
        else:
            uri = f"mongodb://{HOST}:27017/{DATABASE}"

        try:
            self.client = MongoClient(uri)
            self.db = self.client[DATABASE]
            print("You are connected to the database:", self.db.name)
            print("-----------------------------------------------\n")
        except Exception as e:
            print("ERROR: Failed to connect to db:", e)

    def close_connection(self):
        self.client.close()
        print("\n-----------------------------------------------")
        print(f"Connection to {self.db.name}-db is closed")