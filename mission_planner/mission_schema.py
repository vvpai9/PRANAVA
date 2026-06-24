from pydantic import BaseModel, Field, validator
from typing import List, Literal, Tuple, Optional, Union

class Area(BaseModel):
    type: Literal["polygon"]
    coordinates: List[Tuple[float, float]]

    @validator("coordinates", pre=True)
    def repair_coordinates(cls, v):

        repaired = []
        flat = []

        for item in v:

            # case 1: already [lat,lon]
            if isinstance(item, list) and len(item) == 2:
                repaired.append((float(item[0]), float(item[1])))

            # case 2: stray values
            else:
                try:
                    flat.append(float(item))
                except:
                    continue

        # group remaining flat values into pairs
        if len(flat) % 2 != 0:
            raise ValueError("Odd number of coordinate values")

        for i in range(0, len(flat), 2):
            repaired.append((flat[i], flat[i+1]))

        # if len(repaired) < 3:
            # raise ValueError("Polygon must have ≥3 vertices")

        return repaired

        raise ValueError("Coordinates must be list")

    @validator("coordinates")
    def check_min_points(cls, v):
        # if len(v) < 3:
            # raise ValueError("Polygon must have at least 3 points")
        return v

class GridMission(BaseModel):
    mission_type: Literal["grid"]
    area: Area
    altitude: float = Field(..., gt=0)
    passes: int = Field(10, gt=0)
    direction: Literal["horizontal", "vertical"] = "horizontal"
    points_per_pass: int = Field(10, gt=0)
    speed: Optional[float] = Field(None, gt=0)

class SpiralMission(BaseModel):
    mission_type: Literal["spiral_in", "spiral_out"]
    area: Area
    altitude: float = Field(..., gt=0)
    loops: int = Field(..., gt=0)
    points_per_loop: int = Field(..., gt=0)
    speed: Optional[float] = Field(None, gt=0)

class WaypointItem(BaseModel):
    lat: float
    lon: float
    alt: Optional[float] = 25.0
    speed: Optional[float] = None

class WaypointMission(BaseModel):
    mission_type: Literal["waypoint"]
    waypoints: List[WaypointItem]
    speed: Optional[float] = Field(None, gt=0)

MissionParameters = Union[GridMission, SpiralMission, WaypointMission]

def validate_mission(json_data: dict) -> MissionParameters:
    mt = json_data.get("mission_type")
    if mt == "grid":
        return GridMission(**json_data)
    elif mt in ["spiral_in", "spiral_out"]:
        return SpiralMission(**json_data)
    elif mt == "waypoint":
        return WaypointMission(**json_data)
    else:
        raise ValueError(f"Unknown mission type: {mt}")
