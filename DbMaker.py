import os
from datetime import datetime
from pymongo import MongoClient


class DbMaker:
    DATASET_PATH = "dataset/"

    def __init__(self):
        self.connection = MongoClient('mongodb://localhost:27017/')
        self.db = self.connection["test_db"]
        self.labels = self.read_labels()

    def read_labels(self):
        return open(self.DATASET_PATH + "labeled_ids.txt", "r").read().split("\n")

    def create_collections(self):
        """
        This method creates all the collections needed for the project. user, activity and trackpoint
        """
        self.user = self.db["user"]
        self.activity = self.db["activity"]
        self.trackpoint = self.db["trackpoint"]


    def insert_user_collection(self):
        """
        This method insert users into the user tables based on the
        listed user ids in the data directory
        """
        user_ids = os.listdir(self.DATASET_PATH + "Data")
        for user_id in user_ids:
            self.user.insert_one({"_id": user_id, "has_labels": (user_id in self.labels)})


    def insert_activity_collection(self,user_id, transportation_mode, start_date_time, end_date_time):
        """
        This method insert the given parameters to the activity table

        :param user_id: The user id for the person doing the activity
        :param transportation_mode: The type of transportation mode used for this activity
        :param start_date_time: Activity start time
        :param end_date_time: Activity end time

        :return: Returns a generated activity id that can be used in trackpoint reference
        """
        query = """INSERT INTO activity(user_id, transportation_mode, start_date_time, end_date_time) VALUES (%s,%s,%s,%s)"""
        data = {
            "_id": self.activity_count,
            "user_id": user_id,
            "transportation_mode": transportation_mode,
            "start_date_time": start_date_time,
            "end_date_time": end_date_time
        }
        self.activity.insert_one(data)

    def insert_trackpoints(self, filtered_trackpoints):
        """
        This method insert a bulk of filtered trackpoints to the trackpoint collection

        :param filtered_trackpoints: List of trackpoints where we have removed unrelevant info and added activity id
        """
        self.trackpoint.insert_many(filtered_trackpoints)
       

    def filter_trackpoints(self, trackpoints):
        """
        This method filters a bunch of trackpoints to include only relevant info and an activity id.
        The trackpoints are converted to JSON format

        :param trackpoints: trackpoints used to track each user by position, elevation and time
        :param activity_id: The id for the activity the trackpoint corresponds to

        :return: List of trackpoints where we have removed unrelevant info and added activity id
        """
        filtered_trackpoints = []
        for trackpoint in trackpoints:
            formated_date = datetime.strptime(trackpoint[5] + trackpoint[6], "%Y-%m-%d%H:%M:%S")
            data = {
                "_id": self.trackpoint_count,
                "activity_id": self.activity_count,
                "lat": float(trackpoint[0]),
                "lon": float(trackpoint[1]),
                "altitude": float(trackpoint[3]),
                "date": formated_date
            }
            filtered_trackpoints.append(data)
            self.trackpoint_count += 1
        return filtered_trackpoints

    def find_activity_type(self, id, start_time, end_time):
        """
        This method filters a bunch of trackpoints to include only relevant info and an activity id

        :param trackpoints: trackpoints used to track each user by position, elevation and time
        :param activity_id: The id for the activity the trackpoint corresponds to

        :return: List of trackpoints where we have removed unrelevant info and added activity id
        """
        user_labels = open(self.DATASET_PATH + "Data/" + id + "/labels.txt").read().split("\n")
        for label in user_labels[1:-1]:
            attribute = label.split("\t")
            label_start_time = datetime.strptime(attribute[0], "%Y/%m/%d %H:%M:%S")
            label_end_time = datetime.strptime(attribute[1], "%Y/%m/%d %H:%M:%S")
            if start_time == label_start_time and end_time == label_end_time: return attribute[2]
        return None

    def filter_and_insert_activity(self):
        """
        This method filters and inserts activities and trackpoints to the table
        """
        users_list = self.user.find()
        self.activity_count = 0
        self.trackpoint_count = 0
        for user in users_list:
            user_id = user["_id"]
            is_labeled = user["has_labels"]
            activity_filenames = os.listdir(self.DATASET_PATH + "Data/" + user_id + "/Trajectory")
            if len(activity_filenames) == 0: raise TypeError("No activity files found for user", id)
            user_data = []
            for activity_filename in activity_filenames:
                activity_data = read_plt(self.DATASET_PATH + "Data/" + user_id + "/Trajectory/" + activity_filename)
                if activity_data == None: continue
                start_time_activity = datetime.strptime(activity_data[0][5] + " " + activity_data[0][6],
                                                        "%Y-%m-%d %H:%M:%S")
                end_time_activity = datetime.strptime(activity_data[-1][5] + " " + activity_data[-1][6],
                                                      "%Y-%m-%d %H:%M:%S")
                activity_type = None
                if user_id in self.labels:
                    activity_type = self.find_activity_type(user_id, start_time_activity, end_time_activity)
                filtered_trackpoints = self.filter_trackpoints(activity_data)
                self.insert_trackpoints(filtered_trackpoints)
                self.insert_activity_collection(user_id, activity_type, start_time_activity, end_time_activity)
                self.activity_count += 1
        return


def read_plt(file_path):
    """
    Reads the .plt file and formats it as the specification in the task

    :param file_path: the .plt file path
    """
    with open(file_path, 'r') as file:
        lines = file.readlines()
    if len(lines) > 2500 - 6: return None
    data = []
    for line in lines:
        data.append(line.strip().split(','))
    return data[6:]


program = DbMaker()
if program.connection:
    print("Creating tables and inserting data")
    print("This might take a while...")
    print("Wait for the 'Done' message")
    program.create_collections()
    #program.insert_user_collection()
    program.filter_and_insert_activity()
    #program.connection.close()
    print("Done")
