import math
from typing import List, Tuple
from mission_schema import MissionParameters, GridMission, SpiralMission, WaypointMission

def generate_lawnmower_grid(polygon: List[Tuple[float, float]], passes: int, direction: str, points_per_pass: int) -> List[Tuple[float, float]]:
    lats = [p[0] for p in polygon]
    lons = [p[1] for p in polygon]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    
    waypoints = []
    
    if direction == "horizontal":
        lat_step = (max_lat - min_lat) / max(1, passes - 1) if passes > 1 else 0
        lon_step = (max_lon - min_lon) / max(1, points_per_pass - 1) if points_per_pass > 1 else 0
        
        for p in range(passes):
            lat = min_lat + p * lat_step
            lon_range = range(points_per_pass) if p % 2 == 0 else reversed(range(points_per_pass))
            for pt in lon_range:
                lon = min_lon + pt * lon_step
                waypoints.append((lat, lon))
    else:
        lon_step = (max_lon - min_lon) / max(1, passes - 1) if passes > 1 else 0
        lat_step = (max_lat - min_lat) / max(1, points_per_pass - 1) if points_per_pass > 1 else 0
        
        for p in range(passes):
            lon = min_lon + p * lon_step
            lat_range = range(points_per_pass) if p % 2 == 0 else reversed(range(points_per_pass))
            for pt in lat_range:
                lat = min_lat + pt * lat_step
                waypoints.append((lat, lon))
                
    return waypoints

def generate_spiral(polygon: List[Tuple[float, float]], loops: int, points_per_loop: int, spiral_out: bool) -> List[Tuple[float, float]]:
    lats = [p[0] for p in polygon]
    lons = [p[1] for p in polygon]

    # Bounding box
    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)

    max_radius_lat = max(abs(max(lats) - center_lat), abs(min(lats) - center_lat))
    max_radius_lon = max(abs(max(lons) - center_lon), abs(min(lons) - center_lon))

    waypoints = []

    # A spiral from radius=0 (center) up to max_radius (bounds).
    total_points = loops * points_per_loop

    for i in range(total_points):
        # Progress 0.0 to 1.0 representing how far through the spiral we are
        progress = i / max(1, total_points - 1)

        # Angle increases by 2*pi each loop
        angle = progress * loops * 2 * math.pi

        # For spiral_out, radius starts at 0 and grows to 1
        # For spiral_in, radius starts at 1 and shrinks to 0
        radius_factor = progress if spiral_out else (1.0 - progress)

        lat = center_lat + math.sin(angle) * max_radius_lat * radius_factor
        lon = center_lon + math.cos(angle) * max_radius_lon * radius_factor

        waypoints.append((lat, lon))

    return waypoints

def generate_waypoints(mission: MissionParameters) -> List[dict]:
    waypoints = []
    DEFAULT_SPEED = 5.0
    
    if mission.mission_type == "grid":
        coords = generate_lawnmower_grid(mission.area.coordinates, mission.passes, mission.direction, mission.points_per_pass)
        global_speed = mission.speed if mission.speed else DEFAULT_SPEED
        for lat, lon in coords:
            waypoints.append({
                "lat": lat,
                "lon": lon,
                "alt": mission.altitude,
                "speed": global_speed
            })
    elif mission.mission_type in ["spiral_in", "spiral_out"]:
        spiral_out = mission.mission_type == "spiral_out"
        coords = generate_spiral(mission.area.coordinates, mission.loops, mission.points_per_loop, spiral_out)
        global_speed = mission.speed if mission.speed else DEFAULT_SPEED
        for lat, lon in coords:
            waypoints.append({
                "lat": lat,
                "lon": lon,
                "alt": mission.altitude,
                "speed": global_speed
            })
    elif mission.mission_type == "waypoint":
        global_speed = getattr(mission, 'speed', None) or DEFAULT_SPEED
        for wp in mission.waypoints:
            waypoints.append({
                "lat": wp.lat,
                "lon": wp.lon,
                "alt": wp.alt if wp.alt is not None else 25.0,
                "speed": wp.speed if wp.speed is not None else global_speed
            })
            
    return waypoints

def save_to_waypoint_file(waypoints, global_altitude, filename="generated_mission.waypoints"):
    with open(filename, "w") as f:
        f.write("QGC WPL 110\n")

        if not waypoints:
            return

        # TAKEOFF
        home = waypoints[0]
        f.write(f"0\t1\t3\t22\t0\t0\t0\t0\t{home['lat']}\t{home['lon']}\t{global_altitude}\t1\n")

        # WAYPOINTS
        for i, wp in enumerate(waypoints):
            f.write(f"{i+1}\t0\t3\t16\t0\t0\t0\t0\t{wp['lat']}\t{wp['lon']}\t{wp['alt']}\t1\n")

        # RTL
        last = len(waypoints) + 1
        f.write(f"{last}\t0\t3\t20\t0\t0\t0\t0\t0\t0\t0\t1\n")
