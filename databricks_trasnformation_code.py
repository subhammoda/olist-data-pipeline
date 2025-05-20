from pymongo import MongoClient
import pandas as pd
import credentials
from pyspark.sql.functions import col,to_date,datediff,current_date,when

# read the bronze data

base_path = "abfss://olistdata@brazilolistdatastorage.dfs.core.windows.net/bronze/"

orders_path = base_path + "olist_orders_dataset.csv"
payments_path = base_path + "olist_order_payments_dataset.csv"
reviews_path = base_path + "olist_order_reviews_dataset.csv"
items_path = base_path + "olist_order_items_dataset.csv"
customers_path = base_path + "olist_customers_dataset.csv"
sellers_path = base_path + "olist_sellers_dataset.csv"
geolocation_path = base_path + "olist_geolocation_dataset.csv"
products_path = base_path + "olist_products_dataset.csv"


orders_df = spark.read.format("csv").option("header", "true").load(orders_path)
payments_df = spark.read.format("csv").option("header", "true").load(payments_path)
reviews_df = spark.read.format("csv").option("header", "true").load(reviews_path)
items_df = spark.read.format("csv").option("header", "true").load(items_path)
customers_df = spark.read.format("csv").option("header", "true").load(customers_path)
sellers_df = spark.read.format("csv").option("header", "true").load(sellers_path)
geolocation_df = spark.read.format("csv").option("header", "true").load(geolocation_path)
products_df = spark.read.format("csv").option("header", "true").load(products_path)

# getting data from mongodb

uri = "mongodb://" + credentials.mongodb_username + ":" + credentials.mongodb_password + "@" + credentials.mongodb_hostname + ":" + credentials.mongodb_port + "/" + credentials.mongodb_database

client = MongoClient(uri)
mydatabase = client[credentials.mongodb_database]

collection = mydatabase['product_categories']
mongo_data = pd.DataFrame(list(collection.find()))

mongo_data.drop('_id',axis=1,inplace=True)

mongo_sparf_df = spark.createDataFrame(mongo_data)


def clean_datafram(df,name):
    print("Cleaning "+name)
    return df.dropDuplicates().na.drop('all')

orders_df = clean_datafram(orders_df,"Orders")

# Formatting strings to date
orders_df = orders_df.withColumn("order_purchase_timestamp", to_date(col("order_purchase_timestamp")))\
    .withColumn("order_delivered_customer_date", to_date(col("order_delivered_customer_date")))\
        .withColumn("order_estimated_delivery_date", to_date(col("order_estimated_delivery_date")))


# Calculating Delivery and delays
orders_df = orders_df.withColumn("actual_delivery_time", datediff("order_delivered_customer_date", "order_purchase_timestamp"))

orders_df = orders_df.withColumn("estimated_delivery_time", datediff("order_estimated_delivery_date", "order_purchase_timestamp"))

orders_df =orders_df.withColumn("Delay Time", col("actual_delivery_time") - col("estimated_delivery_time"))

# joining respective tables
orders_cutomers_df = orders_df.join(customers_df, orders_df.customer_id == customers_df.customer_id,"left")

orders_payments_df = orders_cutomers_df.join(payments_df, orders_cutomers_df.order_id == payments_df.order_id,"left")

orders_items_df = orders_payments_df.join(items_df,"order_id","left")

orders_items_products_df = orders_items_df.join(products_df, orders_items_df.product_id == products_df.product_id,"left")

final_df = orders_items_products_df.join(sellers_df, orders_items_products_df.seller_id == sellers_df.seller_id,"left")

final_df = final_df.join(mongo_sparf_df,"product_category_name","left")

#removing duplicate columns

def remove_duplicate_columns(df):
    columns = df.columns

    seen_columns = set()
    columns_to_drop = []

    for column in columns:
        if column in seen_columns:
            columns_to_drop.append(column)
        else:
            seen_columns.add(column)
    
    df_cleaned = df.drop(*columns_to_drop)
    return df_cleaned

final_df = remove_duplicate_columns(final_df)


# storing the data in silver block

final_df.write.mode("overwrite").parquet("abfss://olistdata@brazilolistdatastorage.dfs.core.windows.net/silver")