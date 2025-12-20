import fastf1

# session = fastf1.get_session(2025, 1, 'Q')
# event = fastf1.get_event(2025, 1)

# schedule = fastf1.get_event_schedule(2025)
# print(schedule)
# Country = schedule.get_event_by_round(24)
# Country["Country"]
# print(Country)

session = fastf1.get_session(2025, 1, 'R')
session.load()
session.results
print(session.results)