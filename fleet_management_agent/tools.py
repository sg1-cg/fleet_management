import datetime
import decimal
import requests
from google.cloud import bigquery

# Misc db query function
def db_query(query: str):
    try:
        client = bigquery.Client()
        query_job = client.query(query)
        results = query_job.result()
        df = results.to_dataframe()
        data = df.to_dict('records')
        for row in data:
            for key, value in row.items():
                if isinstance(value, datetime.date):
                    row[key] = value.isoformat()
                elif isinstance(value, decimal.Decimal):
                    row[key] = float(value)  # or str(value) to preserve precision as a string
        return data

    except Exception as e:
        error_message = f"An error occured with BigQuery: {e}"
        # Handle errors, potentially fallback to alternate data source
        # Fallback logic would go here if needed
        return {"error": error_message}


# Tools

def recall_query(make: str, model: str, model_year: int):
    """
    Retrieves the recall actions related to the make, model, and model_year provided.

    Args:
        make (str): The vehicle make (e.g., "Audi", "BMW").
        model (str): The vehicle model (e.g., "A4", "X5").
        model_year (int): The model year of the vehicle. (e.g., 2022)

    Returns:
        dict: The recall action data for the specified make, model, and model_year.
    """
    try:
        payload = {'make': make, 'model': model, 'modelYear': model_year}
        r = requests.get('https://api.nhtsa.gov/recalls/recallsByVehicle', params=payload)
        return r.json()
    except Exception as e:
        return {'status': 'Error retrieving recalls.'}


def fleet_query():
    """
    Retrieves the list of vehicle makes, models and model years in the fleet from the database.

    Returns:
        dict: The list of vehicle makes, models and model years in the fleet.
    """
    query = f"""
    SELECT DISTINCT `Make`, `Model`, `Model_Year`
    FROM `EV_Predictive_Maintenance.VEHICLE`
    LIMIT 100
    """
    return db_query(query)


def health_query(vehicle_id: str):
    """
    Retrieves the most recent health data of a vehicle from the database.

    Args:
        vehicle_id (str): The unique identifier of the vehicle.

    Returns:
        dict: The health data of the vehicle.
    """
    query = f"""
    SELECT *
    FROM `EV_Predictive_Maintenance.PM`
    WHERE `Vehicle_ID` = '{vehicle_id}'
    ORDER BY `Timestamp` DESC
    LIMIT 10
    """
    return db_query(query)


def health_bulk_query():
    """
    Retrieves the most recent health data of all vehicles in the fleet from the database.

    Returns:
        dict: The health data of all vehicles in the fleet.
    """
    query = f"""
    select pm1.*
    from `EV_Predictive_Maintenance.PM` pm1
    , (select max(Timestamp) Timestamp, Vehicle_ID from `EV_Predictive_Maintenance.PM` group by Vehicle_ID) pm2
    where pm1.Timestamp=pm2.Timestamp and pm1.Vehicle_ID=pm2.Vehicle_ID
    order by pm1.Timestamp desc
    limit 100
    """
    return db_query(query)


def vehicle_query(vehicle_id: str):
    """
    Retrieves the details of a vehicle from the database.

    Args:
        vehicle_id: a comma separated list of vehicle IDs.

    Returns:
        dict: The details of the vehicle.
    """
    query = f"""
    SELECT *
    FROM `EV_Predictive_Maintenance.VEHICLE`
    WHERE `Vehicle_ID` in '{vehicle_id}'
    """
    return db_query(query)


def part_query():
    """
    Retrieves the vehicle parts from the database.

    Returns:
        dict: The list of vehicle parts.
    """
    query = f"""
    SELECT *
    FROM `EV_Predictive_Maintenance.PART`
    ORDER BY `Name` ASC
    LIMIT 100
    """
    return db_query(query)


def vehicle_appointment_query(vehicle_id: str):
    """
    Retrieves the future service appointments of a vehicle from the database.

    Args:
        vehicle_id (str): The unique identifier of the vehicle.

    Returns:
        dict: The future service appointments of the vehicle.
    """
    query = f"""
    SELECT *
    FROM `EV_Predictive_Maintenance.APPOINTMENT`
    WHERE `Vehicle_ID` = '{vehicle_id}'
    ORDER BY `Time` ASC
    LIMIT 10
    """
    return db_query(query)


def vehicle_rental_query(vehicle_id: str):
    """
    Retrieves the future rental dates of a vehicle from the database.

    Args:
        vehicle_id (str): The unique identifier of the vehicle.

    Returns:
        dict: The future rental dates of the vehicle.
    """
    query = f"""
    SELECT *
    FROM `EV_Predictive_Maintenance.RENTAL`
    WHERE `Vehicle_ID` = '{vehicle_id}'
    AND `Date_From` <= CURRENT_DATE()
    ORDER BY `Date_From` ASC
    LIMIT 10
    """
    return db_query(query)


def part_delivery_time_query(part_id: str):
    """
    Retrieves the current part delivery time in days of a vehicle part from the database.

    Args:
        part_id (str): The unique identifier of the vehicle part.

    Returns:
        dict: the current part delivery time in days of the vehicle part.
    """
    query = f"""
    SELECT `Delivery_Time`
    FROM `EV_Predictive_Maintenance.PART_DELIVERY`
    WHERE `Part_ID` = '{part_id}'
    AND `Valid_From` = (
        SELECT MAX(`Valid_From`)
        FROM `EV_Predictive_Maintenance.PART_DELIVERY`
        WHERE `Part_ID` = '{part_id}'
        AND `Valid_From` <= CURRENT_DATE()
    )
    LIMIT 1
    """
    return db_query(query)


def part_order_query(order_id: str):
    """
    Retrieves the details of the part order from the database.

    Args:
        order_id (str): The unique identifier of the part order.

    Returns:
        dict: The details of the part order.
    """
    query = f"""
    SELECT *
    FROM `EV_Predictive_Maintenance.PART_ORDER`
    WHERE `Order_ID` = '{order_id}'
    ORDER BY `Arrival_Date` DESC
    LIMIT 10
    """
    return db_query(query)


def create_part_order(part_id: str, quantity: int):
    """
    Creates a new part order in the database.

    Args:
        part_id (str): The unique identifier of the vehicle part.
        quantity (int): The quantity of the part to order.

    Returns:
        dict: The details of the created part order.
    """
    query = f"""
    INSERT INTO `EV_Predictive_Maintenance.PART_ORDER` (Order_ID, Part_ID, Amount, Arrival_Date, Last_Update_Time, Price, State)
    select GENERATE_UUID()
    , pd.part_id
    , {quantity}
    , current_date()+pd.Delivery_Time
    , current_timestamp()
    , cast(rand()*(10-10000)+10000 as numeric)
    , 'Pending'
    from `EV_Predictive_Maintenance.PART_DELIVERY` pd
    where pd.valid_from < current_date()
    and pd.part_id = '{part_id}'
    """
    return db_query(query)


def create_appointment(vehicle_id: str, time: str, place: str, order_id: str):
    """
    Creates a new service appointment in the database.

    Args:
        vehicle_id (str): The unique identifier of the vehicle.
        time (str): The date and time of the appointment.
        place (str): The place of the appointment (Country, City, Street).
        order_id (str): The unique identifier of the part order.

    Returns:
        dict: The details of the created appointment.
    """
    query = f"""
    INSERT INTO `EV_Predictive_Maintenance.APPOINTMENT` (Appointment_ID,
        Time,
        Place,
        Order_ID,
        Vehicle_ID)
    VALUES
    ( GENERATE_UUID()
    , '{time}'
    , '{place}'
    , '{order_id}'
    , '{vehicle_id}');
    """
    return db_query(query)


def notify(message: str):
    """
    Sends a notification.

    Args:
        message (str): The message to send.

    Returns:
        dict: The result.
    """
    try:
        return {"status": "success"}
    except Exception as e:
        error_message = f"An error occured with Teams: {e}"
        return {"error": error_message}