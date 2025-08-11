import os
import strawberry
import ephem
import math
from datetime import datetime, timedelta
from math import ceil
from timezonefinder import TimezoneFinder
import pytz
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def dms_to_dd(degrees, minutes, seconds, direction):
    """Convert DMS (degrees, minutes, seconds) to decimal degrees."""
    dd = degrees + minutes / 60 + seconds / 3600
    if direction in ['S', 'W']:
        dd *= -1
    return dd

def calculate_qibla_direction(lat1, long1, lat2, long2):
    """Calculate the Qibla direction given a set of coordinates."""
    delta_long = to_radians(long2 - long1)
    lat1_rad = to_radians(lat1)
    lat2_rad = to_radians(lat2)

    x = math.sin(delta_long) * math.cos(lat2_rad)
    y = math.cos(lat1_rad) * math.sin(lat2_rad) - (math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_long))
    qibla_direction = math.degrees(math.atan2(x, y))

    # Normalize to 0-360 degrees
    qibla_direction = (qibla_direction + 360) % 360

    return qibla_direction

def to_radians(degrees):
    """Convert degrees to radians."""
    return degrees * (math.pi / 180)

def get_timezone_name_and_offset(latitude, longitude, date_time):
    """Get the timezone name and offset in hours for the given location and time."""
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lng=longitude, lat=latitude)
    if timezone_str is None:
        raise ValueError("Could not determine timezone for the provided coordinates.")

    timezone = pytz.timezone(timezone_str)
    utc_offset = timezone.utcoffset(date_time).total_seconds() / 3600

    # Custom handling for Indonesia
    if timezone_str == 'Asia/Makassar':
        timezone_name = timezone_str + ' - WITA'
    elif timezone_str == 'Asia/Jakarta':
        timezone_name = timezone_str + ' - WIB'
    elif timezone_str == 'Asia/Jayapura':
        timezone_name = timezone_str + ' - WIT'
    else:
        timezone_name = timezone_str

    return timezone_name, utc_offset

# Define DMS input type using Strawberry
@strawberry.input
class DMSInput:
    degrees: float
    minutes: float
    seconds: float
    direction: str  # Should be 'N', 'S', 'E', or 'W'

# Define ObservationLocation type using Strawberry
@strawberry.type
class ObservationLocation:
    latitude: str
    longitude: str

# Define ObservationTime type using Strawberry
@strawberry.type
class ObservationTime:
    local_time: str
    utc_time: str
    timezone_offset: str

# Define SolarAzimuthPeriod type using Strawberry
@strawberry.type
class SolarAzimuthPeriod:
    solar_azimuth_int: int
    shadow_azimuth_int: int
    duration_minutes: int
    start_time: str
    end_time: str
    timezone_name: str

# Define SolarPosition type using Strawberry
@strawberry.type
class SolarPosition:
    solar_declination: float
    hour_angle: float
    solar_elevation: float
    solar_azimuth: float
    shadow_azimuth: float
    sun_azimuth_difference: float
    shadow_azimuth_difference: float
    qibla_direction: float
    observation_location: ObservationLocation
    observation_time: ObservationTime
    solar_azimuth_period: SolarAzimuthPeriod

# Define Query type using Strawberry
@strawberry.type
class Query:
    @strawberry.field
    def solar_position(self, lat: DMSInput, lon: DMSInput, date_time: str) -> SolarPosition:
        # Convert the input date_time to a datetime object
        date_time = datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S')

        # Convert DMS to decimal degrees
        observation_latitude = dms_to_dd(lat.degrees, lat.minutes, lat.seconds, lat.direction)
        observation_longitude = dms_to_dd(lon.degrees, lon.minutes, lon.seconds, lon.direction)

        # Get timezone name and offset from location
        timezone_name, timezone_offset = get_timezone_name_and_offset(observation_latitude, observation_longitude, date_time)

        # Convert local time to UTC by subtracting the timezone offset
        utc_time = date_time - timedelta(hours=timezone_offset)
        local_time = date_time  # Local time as provided

        # Set up observer for ephem calculations
        observer = ephem.Observer()
        observer.lat = str(observation_latitude)
        observer.lon = str(observation_longitude)
        observer.elevation = 8  # Set elevation to 8 meters
        observer.date = utc_time.strftime('%Y/%m/%d %H:%M:%S')

        # Calculate the initial position of the sun using ephem
        sun = ephem.Sun(observer)
        initial_solar_azimuth = ceil(sun.az * 180/math.pi)  # Round up to the nearest degree using ceil

        # Calculate Solar Declination and Hour Angle
        solar_declination = sun.dec * 180 / math.pi  # Convert from radians to degrees
        hour_angle = observer.sidereal_time() - sun.ra  # Hour angle in radians
        hour_angle_degrees = hour_angle * 180 / math.pi  # Convert to degrees

        # Normalize Hour Angle to the range -180° to +180°
        if hour_angle_degrees > 180:
            hour_angle_degrees -= 360
        elif hour_angle_degrees < -180:
            hour_angle_degrees += 360

        # Prepare to search until azimuth changes
        matching_times = []

        # Store the initial solar and shadow azimuth for later comparison
        initial_solar_azimuth_precise = sun.az * 180/math.pi
        initial_shadow_azimuth_precise = (initial_solar_azimuth_precise + 180) % 360
        initial_solar_elevation = sun.alt * 180 / math.pi  # Convert from radians to degrees

        # Loop indefinitely until the solar azimuth no longer matches the initial value
        current_time = date_time
        while True:
            # Convert local time to UTC by subtracting the timezone offset
            utc_time_range = current_time - timedelta(hours=timezone_offset)

            # Set up observer for ephem calculations
            observer.date = utc_time_range.strftime('%Y/%m/%d %H:%M:%S')

            # Calculate the position of the sun using ephem
            sun = ephem.Sun(observer)
            solar_azimuth_range = ceil(sun.az * 180 / math.pi)  # Round up to the nearest degree using ceil

            # Check if the solar azimuth is exactly the same as the initial value
            if solar_azimuth_range == initial_solar_azimuth:
                matching_times.append(current_time)
            else:
                break  # Exit the loop if the solar azimuth differs

            # Move to the next minute
            current_time += timedelta(minutes=1)

        # Calculate Qibla direction
        qibla_direction = calculate_qibla_direction(observation_latitude, observation_longitude, 21.4225, 39.8262)
        
        # Calculate the difference between the Solar Azimuth and Qibla Direction
        sun_azimuth_difference = abs(initial_solar_azimuth_precise - qibla_direction)
        sun_azimuth_difference = min(sun_azimuth_difference, 360 - sun_azimuth_difference)  # To account for wrapping around 360°

        # Calculate the difference between the Shadow Azimuth and Qibla Direction
        shadow_azimuth_difference = abs(initial_shadow_azimuth_precise - qibla_direction)
        shadow_azimuth_difference = min(shadow_azimuth_difference, 360 - shadow_azimuth_difference)  # To account for wrapping around 360°

        # Convert decimal degrees back to DMS format for the response
        observation_latitude_dms = f"{lat.degrees}° {lat.minutes}' {lat.seconds}\" {lat.direction}"
        observation_longitude_dms = f"{lon.degrees}° {lon.minutes}' {lon.seconds}\" {lon.direction}"

        # Format timezone offset string
        timezone_offset_str = f"UTC{timezone_offset:+.2f} hours"

        # Calculate duration and format times for solar azimuth period
        if matching_times:
            first_match = matching_times[0]
            last_match = matching_times[-1]
            duration = int((last_match - first_match).total_seconds() // 60) + 1  # Calculate duration in minutes
            
            solar_azimuth_period = SolarAzimuthPeriod(
                solar_azimuth_int=int(initial_solar_azimuth_precise),
                shadow_azimuth_int=int(initial_shadow_azimuth_precise),
                duration_minutes=duration,
                start_time=first_match.strftime('%H:%M:%S'),
                end_time=last_match.strftime('%H:%M:%S %d-%m-%Y'),
                timezone_name=timezone_name
            )
        else:
            solar_azimuth_period = SolarAzimuthPeriod(
                solar_azimuth_int=int(initial_solar_azimuth_precise),
                shadow_azimuth_int=int(initial_shadow_azimuth_precise),
                duration_minutes=0,
                start_time="",
                end_time="",
                timezone_name=timezone_name
            )

        # Return the SolarPosition with all calculated values
        return SolarPosition(
            solar_declination=solar_declination,
            hour_angle=hour_angle_degrees,
            solar_elevation=initial_solar_elevation,
            solar_azimuth=initial_solar_azimuth_precise,
            shadow_azimuth=initial_shadow_azimuth_precise,
            sun_azimuth_difference=sun_azimuth_difference,
            shadow_azimuth_difference=shadow_azimuth_difference,
            qibla_direction=qibla_direction,
            observation_location=ObservationLocation(
                latitude=observation_latitude_dms,
                longitude=observation_longitude_dms
            ),
            observation_time=ObservationTime(
                local_time=f"{local_time.strftime('%Y/%m/%d %H:%M:%S')} ({timezone_name})",
                utc_time=utc_time.strftime('%Y/%m/%d %H:%M:%S'),
                timezone_offset=timezone_offset_str
            ),
            solar_azimuth_period=solar_azimuth_period
        )

# Create the schema using Strawberry
schema = strawberry.Schema(query=Query)

# Initialize FastAPI app and GraphQL
app = FastAPI()
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

# Load the port from .env or default to 8118
port = int(os.getenv("PORT", 8118))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)
