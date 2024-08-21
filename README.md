
# Solar Position and Qibla Direction API

This project is a GraphQL API built using [Strawberry](https://strawberry.rocks/), [FastAPI](https://fastapi.tiangolo.com/), and [PyEphem](https://rhodesmill.org/pyephem/). The API calculates solar positions, shadow directions, the distance to the Kaaba, and Qibla direction based on input coordinates and observation time.

## Features

- Calculate solar declination, hour angle, solar elevation, and azimuth.
- Calculate shadow azimuth.
- Compute the distance to the Kaaba using Vincenty distance.
- Convert and return coordinates in DMS (degrees, minutes, seconds) format.
- Return local time, UTC time, and timezone offset based on the observation coordinates.

## Technologies

- **GraphQL**: Query API via GraphQL queries.
- **Strawberry**: A Python library for building GraphQL APIs.
- **FastAPI**: A modern, fast web framework for building APIs.
- **Ephem**: A library for performing high-precision astronomy calculations.
- **Geopy**: Used for calculating geodesic distances.

## Setup

### Prerequisites

- Python 3.7+
- pip (Python package installer)

### Installation

1. Clone the repository:

   ```bash
   git clone <repository_url>
   cd <repository_directory>
   ```

2. Create a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Copy the `.env-sample` file to `.env`:

   ```bash
   cp .env-sample .env
   ```

5. Open the `.env` file and modify the variables as needed. For example, you can specify the port number for the application:

   ```
   PORT=8880
   ```

The application will now load the environment variables from the `.env` file when running.

### Running the Server

1. Start the FastAPI server using `uvicorn`:

   ```bash
   uvicorn main:app --reload
   ```

   The server will start at `http://localhost:8000/graphql`.

2. Open your browser and visit the following URL to access the GraphQL playground:

   ```
   http://localhost:8000/graphql
   ```

## Usage

### Example Query

You can query the API by providing observation coordinates in DMS (degrees, minutes, seconds) format and a date-time for the observation.

Example GraphQL query:

```graphql
query {
  solarPosition(
    lat: { degrees: 5, minutes: 10, seconds: 55.3, direction: "S" }
    lon: { degrees: 119, minutes: 26, seconds: 27.5, direction: "E" }
    dateTime: "2024-07-16 17:27:00"
  ) {
    solarDeclination
    hourAngle
    solarElevation
    solarAzimuth
    shadowAzimuth
    sunAzimuthDifference
    shadowAzimuthDifference
    distanceToKaaba
    observationLocation {
      latitudeDms
      longitudeDms
    }
    observationTime {
      localTime
      utcTime
      timezoneOffset
    }
  }
}
```

### Response

The API will respond with the solar positioning data, distance to the Kaaba, and formatted observation times.

Example response:

```json
{
  "data": {
    "solarPosition": {
      "solarDeclination": 13.45,
      "hourAngle": 23.12,
      "solarElevation": 45.67,
      "solarAzimuth": 210.45,
      "shadowAzimuth": 30.45,
      "sunAzimuthDifference": 11.23,
      "shadowAzimuthDifference": 45.89,
      "distanceToKaaba": 8650.32,
      "observationLocation": {
        "latitudeDms": "5° 10' 55.3" S",
        "longitudeDms": "119° 26' 27.5" E"
      },
      "observationTime": {
        "localTime": "2024/07/16 17:27:00 (Asia/Makassar)",
        "utcTime": "2024/07/16 09:27:00",
        "timezoneOffset": "UTC+08:00 hours"
      }
    }
  }
}
```

## Project Structure

- **main.py**: The main application file that contains the FastAPI setup, GraphQL schema, and resolvers.
- **requirements.txt**: A list of Python dependencies needed for the project.

## Running in Cluster Mode with PM2

You can run the FastAPI app in cluster mode with multiple instances using `pm2`. This will allow the application to scale across multiple CPU cores.

### Option 1: Using the Ecosystem Configuration

1. Create an `ecosystem.config.js` file with the following content:

   ```js
   module.exports = {
     apps: [
       {
         name: "my-app",            // Name of the app in PM2
         script: "uvicorn",         // Script to run (use uvicorn as the script)
         args: "main:app --reload", // Arguments to pass to uvicorn
         exec_mode: "cluster",      // Cluster mode for multi-node processes
         instances: 3,              // Number of instances (3 nodes)
         interpreter: "python3",    // Python interpreter to use
         watch: true,               // Enable watch mode (optional, for development)
         autorestart: true,         // Auto-restart if the app crashes
         max_memory_restart: "1G",  // Restart if memory usage exceeds 1GB
       }
     ]
   };
   ```

2. Start the application with `pm2` using the ecosystem config file:

   ```bash
   pm2 start ecosystem.config.js
   ```

This will run your `uvicorn` app in cluster mode with 3 instances.

### Option 2: Using the Direct pm2 Command

Alternatively, you can achieve the same result using a direct command:

```bash
pm2 start "uvicorn main:app --reload" --name my-app --interpreter=python3 --instances=3 --exec-mode=cluster
```

### Managing the Cluster

- **Check the status**: You can monitor the status of your instances using:

  ```bash
  pm2 status
  ```

- **Scaling instances**: To scale the number of instances up or down:

  ```bash
  pm2 scale my-app 5  # To scale up to 5 instances
  ```

- **Stopping the app**: You can stop the application with:

  ```bash
  pm2 stop my-app
  ```

- **Restarting the app**: Restart the app with:

  ```bash
  pm2 restart my-app
  ```

Using these steps, `pm2` will manage your FastAPI `uvicorn` server in a clustered environment, distributing the load across multiple nodes.

## License

This project is open source and available under the [MIT License](LICENSE).

## Acknowledgements

- [Strawberry GraphQL](https://strawberry.rocks/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [PyEphem](https://rhodesmill.org/pyephem/)
- [Geopy](https://geopy.readthedocs.io/)
