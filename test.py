from tools.tavily_tool import tavily_search
from tools.flight_tool import search_flights

res = search_flights("plan a 6 days egypt trip from DAC to CAI in December 2024 for 2 adults and 1 child, including flights, hotels, and sightseeing activities. Provide a detailed itinerary with estimated costs and travel tips.")
print(res)