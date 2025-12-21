import fastf1 as ff1
import math

ff1.Cache.enable_cache("cache")


def load_race_data(year, race_num, num_laps=10):
    session = ff1.get_session(year, race_num, "R")
    session.load()
    
    event_info = {
        "name": session.event["EventName"],
        "location": session.event["Location"],
        "date": session.event["EventDate"].strftime("%B %d, %Y")
    }
    
    drivers_data = []
    laps = session.laps

    for drv in session.drivers:
        drv_laps = laps.pick_drivers(drv)
        if len(drv_laps) == 0:
            continue

        driver_info = session.get_driver(drv)
        lap_data = {}
        lap_times = {}
        
        for lap_num in range(1, num_laps + 1):
            lap = drv_laps[drv_laps["LapNumber"] == lap_num]
            if len(lap) > 0:
                try:
                    tel = lap.iloc[0].get_pos_data()
                    if tel is not None and len(tel) > 0:
                        lap_data[lap_num] = tel[["X", "Y", "Time"]].copy()
                        
                        lap_time = lap.iloc[0]["LapTime"]
                        if lap_time is not None and hasattr(lap_time, "total_seconds"):
                            lap_time_seconds = lap_time.total_seconds()
                            if not math.isnan(lap_time_seconds):
                                lap_times[lap_num] = lap_time_seconds
                except:
                    pass

        if lap_data:
            color = driver_info.get("TeamColor", "FFFFFF")
            if not color.startswith("#"):
                color = f"#{color}"

            drivers_data.append({
                "code": drv,
                "abbr": driver_info.get("Abbreviation", drv),
                "team": driver_info.get("TeamName", "Unknown"),
                "color": color,
                "laps": lap_data,
                "lap_times": lap_times,
            })

    return drivers_data, num_laps, event_info
