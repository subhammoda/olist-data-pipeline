import mysql.connector
from mysql.connector import Error
import pandas as pd
import credentials

class MySQLDataIngestion():

    def __init__(self):
        try:
            self.connection = mysql.connector.connect(
                host = credentials.mysql_hostname,
                database = credentials.mysql_database,
                user = credentials.mysql_username,
                password = credentials.mysql_password,
                port = credentials.mysql_port
            )
        except Error as e:
            print("Error while connecting to MySQL", e)

        self.file_path = "./Data/olist_order_payments_dataset.csv"
        self.table_name = "olist_order_payment"

    def create_mysql_db(self):

        try:
            
            if self.connection.is_connected():
                db_Info = self.connection.get_server_info()
                print("Connected to MySQL Server version ", db_Info)
                
                cursor = self.connection.cursor()
                
                cursor.execute(f"DROP TABLE IF EXISTS {self.table_name};")
                print(f"Table {self.table_name} dropped if existed!")

                create_table_query = f"""CREATE TABLE {self.table_name} (
                        order_id VARCHAR(50),
                        payment_sequential INT,
                        payment_type VARCHAR(20),
                        payment_installments INT,
                        payment_value FLOAT
                    );"""
                
                cursor.execute(create_table_query)
                print(f"Table {self.table_name} created successfully!")

                data = pd.read_csv(self.file_path)

                batch_size = 500
                total_records = len(data)

                print(f"Starting data insertion into `{self.table_name}` in batches of {batch_size} records.")
                for start in range(0, total_records, batch_size):
                    end = start + batch_size
                    batch = data.iloc[start:end]

                    # Convert batch to list of tuples for MySQL insertion
                    batch_records = [
                        tuple(row) for row in batch.itertuples(index=False, name=None)
                    ]

                    insert_query = f""" INSERT INTO {self.table_name} (
                    order_id, payment_sequential, payment_type, payment_installments, payment_value
                    ) VALUES (%s, %s, %s, %s, %s);
                    """

                    cursor.executemany(insert_query, batch_records)
                    self.connection.commit()
                    print(f"Inserted records {start + 1} to {min(end, total_records)} successfully.")

                print(f"All {total_records} records inserted successfully into `{self.table_name}`.")

        except Error as e:
            print("Error while connecting to MySQL", e)
        finally:
            if self.connection.is_connected():
                cursor.close()
                self.connection.close()
                print("MySQL connection is closed")

if __name__ == "__main__":
    mysql = MySQLDataIngestion()
    mysql.create_mysql_db()