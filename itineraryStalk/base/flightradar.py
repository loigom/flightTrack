from FlightRadar24.api import FlightRadar24API, Flight
fr_api = FlightRadar24API()

def find_flight(number: str, airline_icao: str = None) -> Flight:
    flights = fr_api.get_flights(airline_icao)
    for flight in flights:
        if flight.number == number:
            details = fr_api.get_flight_details(flight.id)
            flight.set_flight_details(details)
            return flight
