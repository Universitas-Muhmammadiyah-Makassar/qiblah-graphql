
# Qiblah GraphQL - FastAPI with Uvicorn and PM2

This project is a FastAPI application running with Uvicorn and managed by PM2 for process management. The application provides a GraphQL API built using Strawberry, with calculations related to solar positions and Qibla direction.

## Features

- FastAPI app with a GraphQL API using Strawberry.
- Solar position and Qibla direction calculations.
- Uvicorn server with live reloading for development.
- Deployed and managed with PM2 for clustering, auto-restarts, and background execution.
- Custom bash script to start Uvicorn with specific host and port options.
- Environment variables managed using `.env` files.

## Setup

### Prerequisites

- Python 3.7+
- pip (Python package installer)
- PM2 (Process Manager for Node.js, but can manage any script)
- Uvicorn (for running the FastAPI app)

### Installation

1. Clone the repository:

   ```bash
   git clone <repository_url>
   cd <repository_directory>
   ```

2. Create a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create an `.env` file (optional but recommended):

   ```bash
   cp .env-sample .env
   ```

5. Edit `.env` to set your port (default is 8118):

   ```
   PORT=8118
   ```

### Running the Application with PM2

1. **Create the startup script**: Ensure that the `start_uvicorn.sh` script is in your project root with the following content:

   ```bash
   #!/bin/bash
   # Activate the virtual environment
   source ./.venv/bin/activate

   # Run Uvicorn with reload, host, and port options
   exec uvicorn main:app --reload --host 0.0.0.0 --port 8118
   ```

2. **Create the PM2 ecosystem configuration**: Ensure that the `ecosystem.config.js` file is present with the following content:

   ```js
   module.exports = {
       apps: [
         {
           name: "qiblah-graphql",
           script: "./start_uvicorn.sh",  // Run the custom bash script
           exec_mode: "fork",  // Run in fork mode
           interpreter: "/bin/bash",  // Use bash to run the script
         },
       ],
     };
   ```

3. **Make the startup script executable**:

   ```bash
   chmod +x start_uvicorn.sh
   ```

4. **Start the application with PM2**:

   ```bash
   pm2 start ecosystem.config.js
   ```

   This will start the FastAPI application using Uvicorn with the settings defined in the bash script.

5. **Check the application status**:

   ```bash
   pm2 status
   ```

6. **View logs**:

   ```bash
   pm2 logs qiblah-graphql
   ```

### Stopping and Restarting the Application

- **Stop the application**:

  ```bash
  pm2 stop qiblah-graphql
  ```

- **Restart the application**:

  ```bash
  pm2 restart qiblah-graphql
  ```

- **Delete the process**:

  ```bash
  pm2 delete qiblah-graphql
  ```

### Usage

Once the application is running, you can access the GraphQL endpoint at `/graphql`.

#### Example Query:

You can use the following GraphQL query to calculate the solar position and Qibla direction:

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
      latitude
      longitude
    }
    observationTime {
      localTime
      utcTime
      timezoneOffset
    }
  }
}
```

#### Example Response:

The response to the above query might look like this:

```json
{
  "data": {
    "solarPosition": {
      "solarDeclination": "21.24782793044105",
      "hourAngle": "79.6572430421567",
      "solarElevation": "7.804921197597039",
      "solarAzimuth": "292.29977602139326",
      "shadowAzimuth": "112.29977602139326",
      "sunAzimuthDifference": "0.1802781276950327",
      "shadowAzimuthDifference": "179.81972187230497",
      "distanceToKaaba": "9155.546814642335",
      "observationLocation": {
        "latitude": "5.0° 10.0' 55.3" S",
        "longitude": "119.0° 26.0' 27.5" E"
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

### License

This project is open source and available under the [MIT License](LICENSE).

### Acknowledgements

- [Strawberry GraphQL](https://strawberry.rocks/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Uvicorn](https://www.uvicorn.org/)
- [PM2](https://pm2.keymetrics.io/)
