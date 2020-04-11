#!/usr/local/bin/python
# coding: utf8
import datetime
import argparse
## on homeassistant container:
## pip install pymysql
import pymysql
import warnings

def main(args):
  with warnings.catch_warnings():
    warnings.simplefilter("ignore")

    dt = datetime.datetime.today()

    connection = pymysql.connect(
      host=args.host,
      user=args.user,
      password=args.password,
      db=args.db,
      charset="utf8mb4",
      cursorclass=pymysql.cursors.DictCursor
    )

    try:
      with connection.cursor() as cursor:
        sql = """CREATE TABLE IF NOT EXISTS `""" + args.table + """` (
          `date` DATE NOT NULL,
          `value` FLOAT NOT NULL,
          PRIMARY KEY (`date`))
          COLLATE='utf8mb4_unicode_ci'
          ENGINE=InnoDB;"""
        cursor.execute(sql)

        sql = "INSERT INTO `" + args.table + "` (`date`, `value`) VALUES (%s, %s) ON DUPLICATE KEY UPDATE value=%s;"
        cursor.execute(
          sql,
          (
            dt.strftime("%Y-%m-%d"),
            args.value,
            args.value
          )
        )
      
      connection.commit()

    finally:
      connection.close()

    

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Insert kWh value of current day to mariadb database.\nThis creates table if not exists.")
  parser.add_argument('--host', type=str, required=True, help='DB Host')
  parser.add_argument('--user', type=str, required=True, help='DB User')
  parser.add_argument('--password', type=str, required=True, help='DB Password')
  parser.add_argument('--db', type=str, required=True, help='DB Name')
  parser.add_argument('--table', type=str, required=True, help='DB Table')
  parser.add_argument('--value', type=float, required=True, help='Value to insert')
  args = parser.parse_args()
  
  try:
    main(args)
  except IndexError:
    raise ValueError("Argument required")