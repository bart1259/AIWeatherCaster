print("Importing dependencies...")

from backendserver import app
from backendserver.forecaster import get_forecast

if __name__ == '__main__':
    print("Starting server...")

    # Get the forecast so it is cached
    get_forecast(3)
    app.run()