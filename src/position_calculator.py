class PositionCalculator:
    @staticmethod
    def calculate_race_positions(drivers, current_lap, progress):
        positions = []

        for driver in drivers:
            if current_lap not in driver["laps"]:
                positions.append((driver["code"], 999999, 0, 0))
                continue

            tel = driver["laps"][current_lap]
            idx = min(int(progress * (len(tel) - 1)), len(tel) - 1)
            
            cumulative_time = sum(driver["lap_times"].get(i, 0) 
                                 for i in range(1, current_lap))
            
            if current_lap in driver["lap_times"]:
                cumulative_time += driver["lap_times"][current_lap] * progress
            elif current_lap - 1 in driver["lap_times"]:
                cumulative_time += driver["lap_times"][current_lap - 1] * progress

            row = tel.iloc[idx]
            positions.append((driver["code"], cumulative_time, row["X"], row["Y"]))

        positions.sort(key=lambda x: x[1])
        return positions
    
    @staticmethod
    def format_lap_time(drivers, driver_code, current_lap):
        driver = next(d for d in drivers if d["code"] == driver_code)
        if current_lap in driver["lap_times"]:
            try:
                lap_time = driver["lap_times"][current_lap]
                mins, secs = int(lap_time // 60), lap_time % 60
                return f"{mins}:{secs:05.2f}"
            except:
                pass
        return "--:--"
