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
    colname = (args.col if args.col is not None else "value")

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
        sql = """CREATE TABLE IF NOT EXISTS `{table}` (
          `date` DATE NOT NULL,
          `value` FLOAT NULL DEFAULT NULL,
          PRIMARY KEY (`date`))
          COLLATE='utf8mb4_unicode_ci'
          ENGINE=InnoDB;""".format(table=args.table)
        cursor.execute(sql)

        if (colname != 'value'):
          sql = "ALTER TABLE `{table}` ADD COLUMN IF NOT EXISTS `{col}` FLOAT NULL DEFAULT NULL;".format(table=args.table, col=colname)
          cursor.execute(sql)

        sql = "INSERT INTO `{table}` (`date`, `{col}`) VALUES (%s, %s) ON DUPLICATE KEY UPDATE {col}=%s;".format(table=args.table, col=colname)
        sql_data = (dt.strftime("%Y-%m-%d"), args.value, args.value)
        cursor.execute(sql, sql_data)
      
      connection.commit()

    finally:
      connection.close()

    

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Insert kWh value of current day to mariadb database. This creates table if not exists.")
  parser.add_argument('--host', type=str, required=True, help='REQUIRED: DB Host')
  parser.add_argument('--user', type=str, required=True, help='REQUIRED: DB User')
  parser.add_argument('--password', type=str, required=True, help='REQUIRED: DB Password')
  parser.add_argument('--db', type=str, required=True, help='REQUIRED: DB Name')
  parser.add_argument('--table', type=str, required=True, help='REQUIRED: DB Table')
  parser.add_argument('--value', type=float, required=True, help='REQUIRED: Value to insert')
  parser.add_argument('--col', type=str, required=False, help='OPTIONAL: Column name. Defaults to `value`')
  args = parser.parse_args()
  
  try:
    main(args)
  except IndexError:
    raise ValueError("Argument required")