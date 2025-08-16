import pandas as pd
import os 
from sqlalchemy import create_engine
import gc  # Garbage Collector
import logging
import time
logging.basicConfig(
    filename="logs/ingestion_db.log",
    level=logging.DEBUG,
    format="%(asctime)s-%(levelname)s-%(message)s",
    filemode="a"
)
engine=create_engine('sqlite:///inventory.db')

def ingest_db(df,table_name,engine):
    """this function will ingest dataframe into database table"""
    df.to_sql(table_name,con=engine,if_exists="replace",index=False)


def load_raw_data():
    """this fucntion will load the csvs as dataframe and ingest into db"""
    start_time=time.time()
    for file in os.listdir('data'):
        if file.endswith('.csv'):
            df = pd.read_csv(f'data/{file}')
            logging.info(f"ingesting {file} in db")
            ingest_db(df, file[:-4], engine)
            del df
            gc.collect()
    end_time=time.time()
    total=(end_time-start_time)/60
    logging.info('-------Ingestion Complete-----------')
    logging.info(f"Total Time Taken is {total} minutes")


if __name__=="__main__":
    load_raw_data()
