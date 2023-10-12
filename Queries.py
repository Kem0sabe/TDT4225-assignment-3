from collections import Counter
from DbConnector import DbConnector
from haversine import haversine
import datetime
from tabulate import tabulate

class Queries:

    def __init__(self):
        connector = DbConnector(DATABASE='test_db', HOST='localhost', USER='root', PASSWORD='password')
        self.db = connector.db

        self.user = self.db["user"]
        self.activity = self.db["activity"]
        self.trackpoint = self.db["trackpoint"]

    def task_1(self):
        """
        1. How many users, activities and trackpoints are there in the dataset (after it is inserted into the database).
        """
        print("Task 1 - How many users, activities and trackpoints are there in the dataset (after it is inserted into the database).")
        print("Number of users in database: ", self.user.count_documents({}))
        print("Number of activities in database: ", self.activity.count_documents({}))
        print("Number of trackpoints in database: ", self.trackpoint.count_documents({}))
        print()

    def task_2(self):
        """
        2. Find the average number of activities per user
        """
        print("Task 2 - Find the average number of activities per user")
        pipeline = [
            {
                "$group": {
                    "_id": "$user_id",
                    "count": {"$sum": 1}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "average_activities_per_user": {"$avg": "$count"}
                }
            }
        ]

        result = self.activity.aggregate(pipeline)
        average = next(result, None)["average_activities_per_user"]
        print("The average amount of activities per user are:", average)
        print()

    def task_3(self):
        """
        3. Find the top 20 users with the highest number of activities.
        """
        print("Task 3 - Find the top 20 users with the highest number of activities.")
        pipeline = [
            {
                "$group": {
                    "_id": "$user_id",
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"count": -1}
            },
            {
                "$limit": 20
            }
        ]

        result3 = self.activity.aggregate(pipeline)
        print(tabulate(result3, headers="keys", tablefmt="pretty"))
        print()

    def task_4(self):
        """
        4. Find all users who have taken a taxi.
        """
        print("Task 4 - Find all users who have taken a taxi.")
        pipeline = [
            {
                "$match": {"transportation_mode": "taxi"}
            },
            {
                "$group": {
                    "_id": "$user_id",
                }
            }
        ]

        result4 = self.activity.aggregate(pipeline)
        print(tabulate(result4, headers="keys", tablefmt="pretty"))
        print()

    def task_5(self):
        """
        5. Find all types of transportation modes and count how many activities that are tagged with these transportation mode labels. Do not count the rows where the mode is null.
        """
        print("Task 5 - Find all types of transportation modes and count how many activities that are tagged with these transportation mode labels. Do not count the rows where the mode is null.")
        pipeline = [
            {
                "$match": {"transportation_mode": {"$ne": None}}
            },
            {
                "$group": {
                    "_id": "$transportation_mode",
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"count": -1}
            }
        ]

        result5 = self.activity.aggregate(pipeline)
        print(tabulate(result5, headers="keys", tablefmt="pretty"))
        print()

    def task_6(self):
        self._task_6a()
        self._task_6b()

    def _task_6a(self):
        """
        6. a) Find the year with the most activities.
        We assume that if an activity starts in a year, it is to be conted as in that year. In practice, this changes nothing, but there is a teoretical chance of someone starting an activity in one year, and ending it in the next.
        """
        print("Task 6 a - Find the year with the most activities.")
        pipeline = [
            {
                "$project": {
                    "year": {"$year": "$start_date_time"}
                }
            },
            {
                "$group": {
                    "_id": "$year",
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"count": -1}
            },
            {
                "$limit": 1
            }
        ]

        result6a = self.activity.aggregate(pipeline)
        year_most = next(result6a, None)["_id"]
        print("The year with the most activities was", year_most)
        print()

    def _task_6b(self):
        """
        6. b) Is this also the year with most recorded hours?
        Sorting them by total time, we see that 2009 had more total time. To conclude 2008 did not have the most logged hours.
        """
        print("Task 6 b - Is the year with the most activities also the year with most recorded hours?")
        pipeline = [
            {
                "$project": {
                    "year": {"$year": "$start_date_time"},
                    "duration": {
                        "$subtract": ["$end_date_time", "$start_date_time"]
                    }
                }
            },
            {
                "$group": {
                    "_id": "$year",
                    "count": {"$sum": 1},
                    "total_time": {"$sum": "$duration"}
                }
            },
            {
                "$sort": {"total_time": -1}
            },
            {
                "$project": {
                    "_id": 1
                }
            }
        ]

        result6b = self.activity.aggregate(pipeline)
        print(tabulate(result6b, headers="keys", tablefmt="pretty"))
        print()

    def task_7(self):
        """
        7. Find the total distance (in km) walked in 2008, by user with id=112.
        """
        print("Task 7 - Find the total distance (in km) walked in 2008, by user with id=112.")
        activities_found = self.activity.find({
            "user_id": {"$eq": "112"},
            "transportation_mode": {"$eq": "walk"},
            "start_date_time": {"$gte": datetime.datetime(2008, 1, 1), "$lt": datetime.datetime(2009, 1, 1)},
        })

        activity_ids = [act["_id"] for act in activities_found]

        total_distance = 0.0

        for activity_id in activity_ids:
            trackpoints = list(self.trackpoint.find({"activity_id": {"$eq": activity_id}}))
            for i in range(1, len(trackpoints)):
                lat1, lon1 = trackpoints[i - 1]['lat'], trackpoints[i - 1]['lon']
                lat2, lon2 = trackpoints[i]['lat'], trackpoints[i]['lon']
                total_distance += haversine((lat1, lon1), (lat2, lon2))

        print("The total distance in km is:", total_distance)
        print()

    def task_8(self):
        """
        8. Find the top 20 users who have gained the most altitude meters.
        """
        print("Task 8 - Find the top 20 users who have gained the most altitude meters.")
        all_activities = self.activity.find({},{"_id": 1,"user_id": 1})
        all_activity_ids = [(act["_id"],act["user_id"]) for act in all_activities] 

        user_gain = Counter()
        for activity_id,user_id in all_activity_ids:
            trackpoints = list(self.trackpoint.find({"activity_id": {"$eq": activity_id}}))
            for i in range(1, len(trackpoints)):
                difference = trackpoints[i]['altitude'] - trackpoints[i-1]['altitude']
                if difference > 0: user_gain[user_id] += difference

        top20 = sorted(user_gain.items(), key=lambda x: x[1], reverse=True)[:20]
        print(tabulate(top20, headers=["user_id", "total gain (m)"], tablefmt="pretty"))
        print()

    def task_9(self):
        """
        9. Find all users who have invalid activities, and the number of invalid activities per user
        """
        print("Task 9 - Find all users who have invalid activities, and the number of invalid activities per user")
        pipeline = [
            {"$sort": {"date": 1}}
        ]
        trackpoints_sorted = self.trackpoint.aggregate(pipeline)

        illegal_activities = set()
        prev_point = None
        for point in trackpoints_sorted:
            if prev_point == None:
                prev_point = point
                continue
            timediff = (point["date"] - prev_point["date"]).total_seconds()
            if timediff > 60 * 5 and point["activity_id"] == prev_point["activity_id"]:  
                illegal_activities.add(point["activity_id"])
            prev_point = point

        pipeline = [
            {
                "$match": {
                    "_id": {"$in": list(illegal_activities)}
                }
            },
            {
                "$group": {
                    "_id": "$user_id",
                    "count": {"$sum": 1}
                }
            }
        ]

        result9 = self.activity.aggregate(pipeline)
        print(tabulate(result9, headers="keys", tablefmt="pretty"))
        print()

    def task_10(self):
        """
        10.Find the users who have tracked an activity in the Forbidden City of Beijing.
        """
        print("Task 10 - Find the users who have tracked an activity in the Forbidden City of Beijing.")
        beijing_lat = 39.916
        beijing_lon = 116.397
        buffer = 0.0005

        pipeline = [
            {
                "$match": {
                    "lat": {"$gte": beijing_lat - buffer, "$lte": beijing_lat + buffer},
                    "lon": {"$gte": beijing_lon - buffer, "$lte": beijing_lon + buffer}
                }
            },
            {
                "$group": {
                    "_id": "$activity_id"
                }
            },
            {
                "$lookup": {
                    "from": "activity",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "activity_info"
                }
            },
            {
                "$unwind": "$activity_info"
            },
            {
                "$replaceRoot": {"newRoot": "$activity_info"}
            },
            {
                "$group": {
                    "_id": "$user_id",
                    "number_of_illegal": {"$sum": 1}
                }
            }
        ]

        result10 = self.trackpoint.aggregate(pipeline)

        print(tabulate(result10, headers="keys", tablefmt="pretty"))
        print()

    def task_11(self):
        """
        11.Find all users who have registered transportation_mode and their most used transportation_mode.
        """
        print("Task 11 - Find all users who have registered transportation_mode and their most used transportation_mode.")
        pipeline = [
            {
                "$match": {"transportation_mode": {"$ne": None}}
            },
            {
                "$group": {
                    "_id": {
                        "user_id": "$user_id",
                        "transportation_mode": "$transportation_mode"
                    },
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {
                    "_id.user_id": 1,
                    "count": -1
                }
            },
            {
                "$group": {
                    "_id": "$_id.user_id",
                    "most_used": {"$first": "$_id.transportation_mode"}
                }
            },
            {
                "$sort": {
                    "_id": 1  # Optionally, sort by user_id
                }
            }
        ]

        result11 = self.activity.aggregate(pipeline)
        print(tabulate(result11, headers="keys", tablefmt="pretty"))
        print()


