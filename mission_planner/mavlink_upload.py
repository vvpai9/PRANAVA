from pymavlink import mavutil
from typing import List
import time

def upload_mission(waypoints: List[dict], altitude: float, connection_string="/dev/ttyACM0") -> tuple:

    master = mavutil.mavlink_connection(connection_string)
    master.wait_heartbeat()

    master.waypoint_clear_all_send()
    time.sleep(1)

    mission_items = []

    # WP0 (seq 0)
    home = waypoints[0]

    mission_items.append({
        "command": mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
        "lat": home['lat'],
        "lon": home['lon'],
        "alt": 0
    })

    # TAKEOFF (seq 1)
    mission_items.append({
        "command": mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
        "lat": home['lat'],
        "lon": home['lon'],
        "alt": altitude,
        "param1": 15
    })

    # WAYPOINTS (seq 2..N)
    for wp in waypoints[1:]:
        mission_items.append({
            "command": mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
            "lat": wp['lat'],
            "lon": wp['lon'],
            "alt": wp['alt']
        })

    # RTL (seq N+1)
    mission_items.append({
        "command": mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH,
        "lat": 0,
        "lon": 0,
        "alt": 0
    })

    master.waypoint_count_send(len(mission_items))

    for i in range(len(mission_items)):

        msg = master.recv_match(
            type=['MISSION_REQUEST', 'MISSION_REQUEST_INT'],
            blocking=True,
            timeout=10
        )

        if not msg:
            print("Mission upload timeout")
            return False

        seq = msg.seq
        item = mission_items[seq]
        frame = (
            mavutil.mavlink.MAV_FRAME_GLOBAL
            if item["command"] == mavutil.mavlink.MAV_CMD_NAV_TAKEOFF
            else mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT
        )


        master.mav.mission_item_int_send(
            master.target_system,
            master.target_component,
            seq,
            frame,
            item["command"],
            0,
            1,
            item.get("param1", 0),
            item.get("param2", 0),
            item.get("param3", 0),
            item.get("param4", 0),
            int(item["lat"] * 1e7),
            int(item["lon"] * 1e7),
            item["alt"]
        )

    ack = master.recv_match(type='MISSION_ACK', blocking=True, timeout=10)

    mission_ack_map = {
        0: "MISSION_ACCEPTED",
        1: "MISSION_ERROR",
        2: "MISSION_UNSUPPORTED_FRAME",
        3: "MISSION_UNSUPPORTED",
        4: "MISSION_NO_SPACE",
        5: "MISSION_INVALID",
        6: "MISSION_INVALID_PARAM1",
        7: "MISSION_INVALID_PARAM2",
        8: "MISSION_INVALID_PARAM3",
        9: "MISSION_INVALID_PARAM4",
        10: "MISSION_INVALID_PARAM5_X",
        11: "MISSION_INVALID_PARAM6_Y",
        12: "MISSION_INVALID_PARAM7",
        13: "MISSION_INVALID_SEQUENCE",
        14: "MISSION_DENIED"
    }

    if ack:
        result = mission_ack_map.get(ack.type, f"UNKNOWN_ERROR_CODE_{ack.type}")
        print(f"MISSION_ACK: {result}")
        
        if ack.type == mavutil.mavlink.MAV_MISSION_ACCEPTED:
            master.mav.mission_set_current_send(
                master.target_system,
                master.target_component,
                1
            )

            time.sleep(1)

            master.mav.mission_set_current_send(
                master.target_system,
                master.target_component,
                0
            )
            return True, "MISSION_ACCEPTED"
        else:
            return False, result

    return False, "NO_ACK_RECEIVED"
