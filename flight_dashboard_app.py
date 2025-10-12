import streamlit as st
import websocket
import threading
import requests
import datetime
import os

API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")
WEBSOCKET_URL = os.environ.get("WEBSOCKET_URL", "ws://127.0.0.1:8000/airport/socket")
PAGE_TITLE = "Flight Dashboard"

st.set_page_config(layout="wide", page_title=PAGE_TITLE)

def load_custom_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@500;700&display=swap');
            
            .micro-flight-card {
                font-family: 'IBM Plex Sans', sans-serif;
                background-color: #ffffff;
                padding: 10px 12px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
                margin: 5px;
                height: 100px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            }
            
            .micro-flight-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 5px;
            }
            
            .micro-flight-code {
                font-size: 0.9em;
                font-weight: 700;
                color: #2c3e50;
            }
            
            .micro-status {
                font-size: 0.7em;
                font-weight: 700;
                padding: 2px 6px;
                border-radius: 4px;
            }
            
            .status-ontime {
                background-color: #e6f7e8;
                color: #2e7d32;
            }
            
            .status-delayed {
                background-color: #fcebeb;
                color: #c0392b;
            }
            
            .micro-details {
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .micro-airport-info {
                text-align: center;
            }
            
            .micro-airport-code {
                font-size: 1.2em;
                font-weight: 700;
                color: #34495e;
            }
            
            .micro-time {
                font-size: 0.7em;
                color: #95a5a6;
                white-space: nowrap;
            }
            
            .micro-arrow {
                font-size: 1em;
                color: #bdc3c7;
            }
        </style>
    """, unsafe_allow_html=True)

def micro_flight_card(flight_data):
    """
    Creates a small flight card using HTML/CSS.
    :param flight_data: Dictionary containing flight details.
    """
    status_class = "status-ontime" if flight_data['status'].lower() == "on time" else "status-delayed"
    st.markdown(f"""
        <div class="micro-flight-card">
            <div class="micro-flight-header">
                <span class="micro-flight-code">{flight_data['code']}</span>
                <span class="micro-status {status_class}">{flight_data['status']}</span>
            </div>
            <div class="micro-details">
                <div class="micro-airport-info">
                    <div class="micro-airport-code">{flight_data['source']}</div>
                    <div class="micro-time">{flight_data['dep']}</div>
                </div>
                <div class="micro-arrow">→</div>
                <div class="micro-airport-info">
                    <div class="micro-airport-code">{flight_data['dest']}</div>
                    <div class="micro-time">{flight_data['arr']}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def format_datetime_utc(date_string):
    
    try:
        dt_object = datetime.datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")
        dt_object += datetime.timedelta(hours=5,minutes=30)
        return dt_object.strftime("%b %d, %I:%M %p IST")
    except ValueError:
        return "N/A"

class FlightDataFetcher:
    
    @st.cache_data(ttl=120)
    def top_flights(_self, airport='', count=15):
        """Fetches top flights from the API."""
        try:
            response = requests.get(f"{API_BASE_URL}/get_flights", params={'airport': airport, "count": count})
            response.raise_for_status()  
            flights_raw = response.json()
            processed_flights = [
                {
                    "code": f['code'],
                    "source": f['source'],
                    "dest": f['destination'],
                    "dep": format_datetime_utc(f['departure_time']),
                    "arr": format_datetime_utc(f['arrival_time']),
                    "status": f['state']
                } for f in flights_raw
            ]
            return processed_flights
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching top flights: {e}")
            return []

    @st.cache_data(ttl=30)
    def get_all_airports(_self):
        try:
            response = requests.get(f"{API_BASE_URL}/all_airports")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching all airports: {e}")
            return {}

class WebSocketClient:
    """Manages the WebSocket connection and message queue."""
    def __init__(self, url):
        self.url = url
        self.ws = None
        self.thread = None
        self.is_running = False
        self.message_queue = []
        self.lock = threading.Lock()
        
    def _on_message(self, ws, message):
        with self.lock:
            self.message_queue.append(message)
    
    def _on_error(self, ws, error):
        st.error(f"WebSocket Error: {error}")
        
    def _on_close(self, ws, close_status_code, close_msg):
        print(f"WebSocket connection closed. Code: {close_status_code}, Msg: {close_msg}")
        self.is_running = False
    
    def _on_open(self, ws):
        """Callback for successful WebSocket connection."""
        print("WebSocket connection opened.")
        self.is_running = True
    
    def run_forever(self):
        """Runs the WebSocket client in a loop."""
        self.ws = websocket.WebSocketApp(
            self.url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        self.ws.run_forever()
        
    def start(self):
        """Starts the WebSocket client thread."""
        if not self.is_running:
            self.thread = threading.Thread(target=self.run_forever, daemon=True)
            self.thread.start()
            
    def get_messages(self):
        """Returns and clears the message queue in a thread-safe manner."""
        with self.lock:
            messages = list(self.message_queue)
            self.message_queue.clear()
            return messages

class FlightDashboardApp:
    def __init__(self):
        if "websocket_client" not in st.session_state:
            st.session_state.websocket_client = WebSocketClient(WEBSOCKET_URL)
        if "messages" not in st.session_state:
            st.session_state.messages = []
            
        self.ws_client = st.session_state.websocket_client
        self.data_fetcher = FlightDataFetcher()
        self.num_columns = 4

    def run(self):
        load_custom_css()
        st.title("Flight Dashboard ✈️")
        
        self.display_flight_grid()
        
        self.ws_client.start()

        st.subheader("Real-time Updates")
        self.realtime_updates_fragment()

    def display_flight_grid(self):

        flights_to_display = self.data_fetcher.top_flights()
        cols = st.columns(self.num_columns)
        for i, flight in enumerate(flights_to_display):
            with cols[i % self.num_columns]:
                micro_flight_card(flight)
    
    @st.fragment(run_every="1s")
    def realtime_updates_fragment(self):
        new_messages = self.ws_client.get_messages()
        
        if new_messages:
            st.session_state.messages.extend(new_messages)
            
        # Display the latest messages
        display_messages = st.session_state.messages[-15:]
        for msg in display_messages:
            st.write(msg)
            
        if not st.session_state.messages:
            st.info("Waiting for real-time updates...")

# --- Main execution block ---
if __name__ == "__main__":
    app = FlightDashboardApp()
    app.run()



# def get_interpolated_point(start_lat, start_lon, end_lat, end_lon, fraction):
#     """
#     Calculates an interpolated point on a great-circle path.
#     :param start_lat: Latitude of the starting point.
#     :param start_lon: Longitude of the starting point.
#     :param end_lat: Latitude of the destination.
#     :param end_lon: Longitude of the destination.
#     :param fraction: Fraction of the journey completed (0.0 to 1.0).
#     :return: Tuple (latitude, longitude) of the interpolated point.
#     """
    
#     # Convert to radians
#     lat1, lon1 = math.radians(start_lat), math.radians(start_lon)
#     lat2, lon2 = math.radians(end_lat), math.radians(end_lon)

#     # Great circle angular distance
#     delta_lon = lon2 - lon1
#     a = math.sin(lat1) * math.sin(lat2) + math.cos(lat1) * math.cos(lat2) * math.cos(delta_lon)
#     delta = math.acos(a)
    
#     if delta == 0:
#         return (start_lat, start_lon)

#     # Intermediate position formula
#     A = math.sin((1 - fraction) * delta) / math.sin(delta)
#     B = math.sin(fraction * delta) / math.sin(delta)
    
#     x = A * math.cos(lat1) * math.cos(lon1) + B * math.cos(lat2) * math.cos(lon2)
#     y = A * math.cos(lat1) * math.sin(lon1) + B * math.cos(lat2) * math.sin(lon2)
#     z = A * math.sin(lat1) + B * math.sin(lat2)
    
#     new_lat = math.atan2(z, math.sqrt(x**2 + y**2))
#     new_lon = math.atan2(y, x)
    
#     return (math.degrees(new_lat), math.degrees(new_lon))
