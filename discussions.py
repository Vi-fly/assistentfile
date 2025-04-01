import os
from pymongo import MongoClient
from dotenv import load_dotenv
from urllib.parse import quote_plus
from bson import ObjectId

load_dotenv()

# Get raw credentials from environment
raw_username = os.getenv("MONGO_USER")
raw_password = os.getenv("MONGO_PASS")
cluster = os.getenv("MONGO_CLUSTER")  # e.g. cluster0.mongodb.net
db_name = os.getenv("MONGO_DB", "discussions_db")

# Encode username & password
username = quote_plus(raw_username)
password = quote_plus(raw_password)

# Construct secure URI
MONGO_URI = f"mongodb+srv://{username}:{password}@{cluster}/{db_name}?retryWrites=true&w=majority"

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[db_name]
posts_collection = db["posts"]

# Get all posts sorted by newest
def get_all_posts():
    return posts_collection.find().sort("_id", -1)

# Add a new post
def add_post(username, content, image_data=None, video_data=None):
    post = {
        "username": username,
        "content": content,
        "likes": 0,
        "comments": []
    }
    if image_data:
        post["image"] = image_data
    if video_data:
        post["video"] = video_data
    posts_collection.insert_one(post)

# Add a like to a post
def add_like(post_id):
    posts_collection.update_one({"_id": ObjectId(post_id)}, {"$inc": {"likes": 1}})

# Add a comment to a post
def add_comment(post_id, comment):
    posts_collection.update_one({"_id": ObjectId(post_id)}, {"$push": {"comments": comment}})

def delete_post(post_id):
    """Delete a post by its ID."""
    posts_collection = db["posts"]
    posts_collection.delete_one({"_id": post_id})
