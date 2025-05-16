from pymongo import MongoClient
import pandas as pd
import credentials

class MongoDBDataIngestion():

    def __init__(self):

        self.uri = "mongodb://" + credentials.mongodb_username + ":" + credentials.mongodb_password + "@" + credentials.mongodb_hostname + ":" + credentials.mongodb_port + "/" + credentials.mongodb_database
        self.client = MongoClient(self.uri)
        self.file_path = "./Data/product_category_name_translation.csv"
        self.table_name = "olist_product_category"

    def create_mongodb_db(self):

        try:
            if self.client:
                print("Connection established successfully!")
            db = self.client[credentials.mongodb_database]
            collection = db[self.table_name] 

            data = pd.read_csv(self.file_path)
            data_to_insert = data.to_dict(orient="records")

            collection.insert_many(data_to_insert)
            print("Data uploaded to MongoDB successfully!")

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            if self.client:
                self.client.close()

if __name__ == "__main__":
    mongo = MongoDBDataIngestion()
    mongo.create_mongodb_db()