# ha-daily-insert-mysql
Designed to work with Home Assistant, but you can really use it wherever you want.
This script publishes a value into a mysql table with the current date (per day), if date already exists, it'll overwrite the value.
If table doesn't exist, it'll create.

This is very useful to have long time data with very low disk usage database.
Instead of recording the whole changes throughout the day, you only have a single value per day.

**Note that it only accepts the value as FLOAT**
I expect to implement it to more datatypes in some future

**Ensure you have the database created, it only creates the table.**

## What can I do with this?
Useful for:
- publish daily values of current energy meter
- publish an average of the temperature of the current day
- publish if irrigation has started today or not **(Remember: this only allows float values, until for now. So for this it needs 0.0 or 1.0 for example)**
- etc...

## Usage
`python3 daily_insert_mysql.py --host=db_host(ip or hostname) --user=your_user --password=your_password --db=your_db --table=your_table --value your_value`

## Example with code for home assistant
Here's an example to record a sensor value of the current electricity meter.
This sensor resets everyday, so we'll publish it whenever the sensor changes it's state.

### Configuration for MariaDB Addon
This is to create the database, user and permissions into the addon

```
databases:
  - custom_data
logins:
  - username: custom_data_user
    host: '%'
    password: teste
rights:
  - username: custom_data_user
    host: '%'
    database: custom_data
    grant: ALL PRIVILEGES ON
```

### Insert values

First `shell_command` is to install the dependency needed for the python script to work. More below we will create an automation to run it every startup.
```
shell_command:
  python_install_pymysql_dependency: "pip install pymysql"
  energy_daily_insert: "python3 /config/daily_insert_mysql.py --host=core-mariadb --user=custom_data_user --password=teste --db=custom_data --table=energy_kwh --value {{ states.sensor.energy_daily_kwh.state }}"
```

First `automation` is to install the dependency needed at startup. If it exist, it'll ignore, if not, it'll install.
Second `automation`, everytime sensor changes its value. Publish it with current date.
```
automation:
  - alias: "Energy install python pymysql dependency at startup"
    initial_state: true
    trigger:
      - platform: homeassistant
        event: start
    action:
      - service: shell_command.python_install_pymysql_dependency
  - alias: "Energy daily update total kw"
    initial_state: true
    trigger:
      - platform: state
        entity_id: sensor.energy_daily_kwh
    action:
      - service: shell_command.energy_daily_insert
```

### How can I return the values?

You can use the [Home Assistant SQL integration](https://www.home-assistant.io/integrations/sql/) to get the values from the database

If you dive into SQL Queries, you will understand that you can do a lot of things with it.
This is a very simple example.
```
sensor:
  - platform: sql
    db_url: mysql://user:password@localhost/custom_data
    queries:
      - name: Sql value
        query: "SELECT `value` FROM energy WHERE `date` = '2020-04-10';"
        column: 'value'
        unit_of_measurement: 'kWh'
```