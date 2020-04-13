# ha-daily-insert-mysql
Designed to work with Home Assistant, but you can really use it wherever you want.
This script publishes a value into a mysql table with the current date (per day), if date already exists, it'll overwrite the value.
If table doesn't exist, it'll create.

This is very useful to have long time data with very low disk usage database.
Instead of recording the whole changes throughout the day, you only have a single value per day.

**For most of people, this could be a replacement to InfluxDB.**

**Note that it only accepts the value as FLOAT**

**Ensure you have the database created, it only creates the table.**

## TOC
- [What can I do with this?](#what-can-i-do-with-this-)
- [Usage](#usage)
- [Example with code for home assistant](#example-with-code-for-home-assistant)
  - [Configuration for MariaDB Addon](#configuration-for-mariadb-addon)
  - [Insert values](#insert-values)
  - [How can I return the values?](#how-can-i-return-the-values-)
    - [Method 1: Home Assistant](#method-1--home-assistant)
    - [Method 2: Grafana](#method-2--grafana)
- [Insert values into different column names in the same table](#insert-values-into-different-column-names-in-the-same-table)
- [Pro tip: Use template shell_command](#pro-tip--use-template-shell-command)

## What can I do with this?
With 365 rows of data, neither 500KB you'll use :boom:

This is what you achieve

| date | value |
| ------ | ------- |
| 2020-04-06 | 15.5 |
| 2020-04-07 | 16 |
| 2020-04-08 | 14.8 |
| 2020-04-09| 11.2 |
| 2020-04-10 | 15.4 |

Useful for:
- publish daily values of current energy meter
- publish an *average*, *max* or *min* of the temperature of the current day
- keep track of how many hours you watch tv for a day
- publish if irrigation has started today or not **(Remember: this only allows float values. So for this it needs 0.0 or 1.0 for example)**
- etc... be creative...

:star: **[Optional]** you can have multiple columns and add the value to the column you want. [See this](#insert-values-into-different-column-names-in-the-same-table)

If not mention `--col`, default column name is `value`

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

Use your own `username` and `password`

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
#### Method 1: Home Assistant
You can use the [Home Assistant SQL integration](https://www.home-assistant.io/integrations/sql/) to get the values from the database

If you dive into SQL Queries, you will understand that you can do a lot of things with it.
This is a very simple example.
```
sensor:
  - platform: sql
    db_url: mysql://user:password@localhost/custom_data
    queries:
      - name: Sql value
        query: "SELECT `value` FROM energy_kwh WHERE `date` = '2020-04-10';"
        column: 'value'
        unit_of_measurement: 'kWh'
```

#### Method 2: Grafana
You can use MySQL databases in Grafana, just like InfluxDB, but instead you'll have a very compact database.

## Insert values into different column names in the same table

There's an optional argument `--col` which you can use it to mention to which column you want to save the value to.
The column is added automatically if you specify the argument, if not it'll ignore it.
If you created the table by yourself, ensure the other columns instead of the date has `ALLOW NULL` and `DEFAULT NULL`. If the table was created by this script, you don't need to worry.

This was tested on MariaDB, I'm not sure if it'll work with MySQL versions

Example:
`python3 daily_insert_mysql.py --host=core-mariadb --user=data_energy --password=teste --db=custom_data --table=energy_kwh --value 3.4 --col fridge`

## Pro tip: Use template shell_command
```
automation:
  - alias: "Energy daily insert values to database"
    initial_state: true
    trigger:
      - platform: state
        entity_id: sensor.energy_daily_simples
      - platform: state
        entity_id: sensor.energy_daily_fridge
      - platform: state
        entity_id: sensor.energy_daily_dishwasher
      - platform: state
        entity_id: sensor.energy_daily_drying_machine
      - platform: state
        entity_id: sensor.energy_daily_washing_machine
      - platform: state
        entity_id: sensor.energy_daily_hot_water_tank
    action:
      - service: shell_command.daily_insert_mysql_template
        data_template:
          table: energy_kwh
          value: >
            {{ trigger.to_state.state }}
          column: >
            {% if trigger.entity_id == "sensor.energy_daily_simples" %}
              total
            {% elif trigger.entity_id == "sensor.energy_daily_fridge" %}
              fridge
            {% elif trigger.entity_id == "sensor.energy_daily_dishwasher" %}
              dishwasher
            {% elif trigger.entity_id == "sensor.energy_daily_drying_machine" %}
              drying_machine
            {% elif trigger.entity_id == "sensor.energy_daily_washing_machine" %}
              washing_machine
            {% elif trigger.entity_id == "sensor.energy_daily_hot_water_tank" %}
              hot_water_tank
            {% endif %}

shell_command:
  daily_insert_mysql: "python3 /config/py_scripts/daily_insert_mysql.py --host=core-mariadb --user=data_energy --password=teste --db=custom_data --table={{ table }} --value={{ value }} {{ '--col='+column if column is defined }}"
```
