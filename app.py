import strawberry
import ephem
import math
from datetime import datetime, timedelta
from timezonefinder import TimezoneFinder
import pytz
from geopy.distance import geodesic

# Utility functions
def dms_to_dd(degrees, minutes, seconds, direction):
    dd = degrees + minutes / 60 + seconds / 3600
    if direction in ['S', 'W']:
        dd *= -1
    return dd

def calculate_qibla_direction(lat1, long1, lat2, long2):
    delta_long = to_radians(long2 - long1)
    lat1_rad = to_radians(lat1)
    lat2_rad = to_radians(lat2)

    x = math.sin(delta_long) * math.cos(lat2_rad)
    y = math.cos(lat1_rad) * math.sin(lat2_rad) - (math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_long))
    qibla_direction = math.degrees(math.atan2(x, y))
    qibla_direction = (qibla_direction + 360) % 360

    return qibla_direction

def to_radians(degrees):
    return degrees * (math.pi / 180)

def get_timezone_name_and_offset(latitude, longitude, date_time):
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lng=longitude, lat=latitude)
    if timezone_str is None:
        raise ValueError("Could not determine timezone for the provided coordinates.")
    timezone = pytz.timezone(timezone_str)
    utc_offset = timezone.utcoffset(date_time).total_seconds() / 3600
    return timezone_str, utc_offset

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
    distance_to_kaaba: float
    observation_location: ObservationLocation
    observation_time: ObservationTime

# Define Query type using Strawberry
@strawberry.type
class Query:
    @strawberry.field
    def solar_position(self, lat: DMSInput, lon: DMSInput, date_time: str) -> SolarPosition:
        # Convert the input date_time to a datetime object
        date_time = datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S')

        # Convert DMS to decimal degrees
        lat_dd = dms_to_dd(lat.degrees, lat.minutes, lat.seconds, lat.direction)
        lon_dd = dms_to_dd(lon.degrees, lon.minutes, lon.seconds, lon.direction)

        # Get timezone name and offset
        timezone_name, timezone_offset = get_timezone_name_and_offset(lat_dd, lon_dd, date_time)

        # Convert local time to UTC by subtracting the timezone offset
        utc_time = date_time - timedelta(hours=timezone_offset)

        # Set up observer for ephem calculations
        observer = ephem.Observer()
        observer.lat = str(lat_dd)
        observer.lon = str(lon_dd)
        observer.elevation = 8  # Set elevation to 8 meters
        observer.date = utc_time.strftime('%Y/%m/%d %H:%M:%S')

        # Calculate the position of the sun
        sun = ephem.Sun(observer)
        solar_declination = sun.dec * 180 / math.pi
        hour_angle = observer.sidereal_time() - sun.ra
        hour_angle_degrees = hour_angle * 180 / math.pi
        if hour_angle_degrees > 180:
            hour_angle_degrees -= 360
        elif hour_angle_degrees < -180:
            hour_angle_degrees += 360

        solar_azimuth = sun.az * 180 / math.pi
        shadow_azimuth = (solar_azimuth + 180) % 360
        solar_elevation = sun.alt * 180 / math.pi

        # Calculate Qibla direction
        qibla_direction = calculate_qibla_direction(lat_dd, lon_dd, 21.4225, 39.8262)

        # Calculate the differences between solar/shadow azimuth and Qibla direction
        sun_azimuth_difference = abs(solar_azimuth - qibla_direction)
        sun_azimuth_difference = min(sun_azimuth_difference, 360 - sun_azimuth_difference)
        shadow_azimuth_difference = abs(shadow_azimuth - qibla_direction)
        shadow_azimuth_difference = min(shadow_azimuth_difference, 360 - shadow_azimuth_difference)

        # Calculate Vincenty distance to Kaaba
        kaaba_location = (21.4225, 39.8262)
        current_location = (lat_dd, lon_dd)
        distance_to_kaaba = geodesic(current_location, kaaba_location).kilometers

        # Convert decimal degrees back to DMS format for the response
        observation_latitude_dms = f"{lat.degrees}° {lat.minutes}' {lat.seconds}\" {lat.direction}"
        observation_longitude_dms = f"{lon.degrees}° {lon.minutes}' {lon.seconds}\" {lon.direction}"

        # Format timezone offset string
        offset_hours = int(timezone_offset)
        offset_minutes = int((timezone_offset - offset_hours) * 60)
        timezone_offset_str = f"UTC{offset_hours:+03d}:{offset_minutes:02d} hours"

        # Return the SolarPosition with observation location and times
        return SolarPosition(
            solar_declination=solar_declination,
            hour_angle=hour_angle_degrees,
            solar_elevation=solar_elevation,
            solar_azimuth=solar_azimuth,
            shadow_azimuth=shadow_azimuth,
            sun_azimuth_difference=sun_azimuth_difference,
            shadow_azimuth_difference=shadow_azimuth_difference,
            distance_to_kaaba=distance_to_kaaba,
            observation_location=ObservationLocation(
                latitude=observation_latitude_dms,
                longitude=observation_longitude_dms
            ),
            observation_time=ObservationTime(
                local_time=f"{date_time.strftime('%Y/%m/%d %H:%M:%S')} ({timezone_name})",
                utc_time=utc_time.strftime('%Y/%m/%d %H:%M:%S'),
                timezone_offset=timezone_offset_str
            )
        )

# Create the schema using Strawberry
schema = strawberry.Schema(query=Query)

# Example using FastAPI to serve the GraphQL API
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

app = FastAPI()
graphql_app = GraphQLRouter(schema)

app.include_router(graphql_app, prefix="/graphql")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8880)