# PRANAVA

## Prompt-driven Route Generation for Autonomous Navigation of Aerial Vehicles using Generative AI

PRANAVA is a prompt-driven UAV mission planning framework that converts natural language mission descriptions into executable MAVLink missions using a locally hosted Large Language Model (LLM).

The system allows users to generate autonomous waypoint, grid survey, and spiral survey missions through a conversational interface without manually creating mission waypoints in traditional Ground Control Station software.

The generated missions are automatically validated, converted into MAVLink mission items, and uploaded to ArduPilot-based autopilots for execution.

---

## Features

- Natural language mission planning
- Locally hosted Mistral LLM using Ollama
- Grid survey mission generation
- Spiral-in survey mission generation
- Spiral-out survey mission generation
- Waypoint mission generation
- MAVLink mission upload
- ArduPilot SITL integration
- QGroundControl compatibility
- Pixhawk compatibility
- Fully offline operation

---

## Supported Mission Types

### Grid Survey

Example:

```text
Generate a horizontal grid survey mission
within the specified area at 25 m altitude
with 5 passes and 5 waypoints per pass.
```

<img width="1910" height="1023" alt="Screenshot_20260526_195555" src="https://github.com/user-attachments/assets/14934ae7-6c21-4e44-accd-304c50754f3b" />

### Spiral Survey

Example:

```text
Generate a spiral out survey mission
within the specified area
with 3 loops at 25 m altitude.
```

<img width="1920" height="1080" alt="Screenshot_20260526_204458" src="https://github.com/user-attachments/assets/59d5e535-c01a-465f-8bd7-796f15c69c98" />

### Waypoint Mission

Example:

```text
Generate a waypoint mission through
15.3676,75.1252
15.3669,75.1260
15.3665,75.1255
at 20 m altitude.
```

---

## Prerequisites

Install the following software before proceeding:

- Ubuntu Linux 22.04 or newer
- Python 3.10+
- Git
- Ollama
- ArduPilot SITL
- MAVProxy
- QGroundControl

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/vvpai9/PRANAVA.git

cd PRANAVA/mission_planner
```

### 2. Create Python Virtual Environment

```bash
python3 -m venv venv
```

Activate the environment:

```bash
source venv/bin/activate
```

### 3. Install Dependencies

Upgrade pip:

```bash
pip install --upgrade pip
```

Install project dependencies:

```bash
pip install PyQt5 requests pydantic pymavlink
```

---

## Install Ollama

Install Ollama:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Verify installation:

```bash
ollama --version
```

---

## Download the Mistral Model

Pull the model:

```bash
ollama pull mistral
```

Start Ollama:

```bash
ollama serve
```

Verify:

```bash
ollama list
```

---

## Install ArduPilot SITL

Clone ArduPilot:

```bash
git clone https://github.com/ArduPilot/ardupilot.git

cd ardupilot
```

Initialize submodules:

```bash
git submodule update --init --recursive
```

Install prerequisites:

```bash
Tools/environment_install/install-prereqs-ubuntu.sh -y
```

Reload environment variables:

```bash
. ~/.profile
```

Configure and build SITL:

```bash
./waf configure --board sitl

./waf copter
```

---

## Launch ArduPilot SITL

Start ArduCopter SITL:

```bash
sim_vehicle.py -v ArduCopter --console --map --out=127.0.0.1:14550 --out=127.0.0.1:14551
```

Port assignments:

| Port | Application |
|--------|--------|
| 14550 | QGroundControl |
| 14551 | PRANAVA |

---

## Launch QGroundControl

Open QGroundControl.

The software should automatically connect to SITL through:

```text
127.0.0.1:14550
```

Verify:

- Vehicle appears on map
- GPS lock is obtained
- Mission planning interface is accessible

---

## Run PRANAVA

Navigate to the project directory:

```bash
cd PRANAVA/mission_planner
```

Activate the virtual environment:

```bash
source venv/bin/activate
```

Launch the application:

```bash
python3 main.py
```

---

## Example Workflow

Prompt:

```text
Generate a horizontal grid survey mission
(15.3676,75.1252)
(15.3676,75.1260)
(15.3668,75.1260)
(15.3668,75.1252)

Altitude 25 m
5 passes
5 waypoints per pass
```

PRANAVA will:

1. Extract mission parameters.
2. Validate mission schema.
3. Generate survey waypoints.
4. Create MAVLink mission items.
5. Upload the mission to ArduPilot.
6. Display mission status in the user interface.
7. Enable mission visualization in QGroundControl.

---

## Technologies Used

| Component | Technology |
|------------|------------|
| Programming Language | Python |
| GUI Framework | PyQt5 |
| LLM Runtime | Ollama |
| Language Model | Mistral |
| Validation Engine | Pydantic |
| MAVLink Library | pymavlink |
| Flight Stack | ArduPilot |
| Ground Control Station | QGroundControl |
| Simulation Platform | SITL |
| Flight Controller | Pixhawk 2.4.8 |

---

## Experimental Validation

### Software-in-the-Loop (SITL)

- Grid survey missions
- Spiral survey missions
- Waypoint missions
- MAVLink mission uploads
- Autonomous mission execution

### Hardware Validation

- Pixhawk 2.4.8
- M8N GNSS Receiver
- Autonomous takeoff
- Mission execution
- Return-to-Launch verification

---

## Results

| Metric | Result |
|----------|----------|
| Supported Mission Types | 4 |
| SITL Missions Tested | 20+ |
| Real Flight Tests | 10+ |
| Local AI Inference | Yes |
| Offline Operation | 100% |
| MAVLink Compatibility | Yes |
| Mission Planning Time Reduction | 59% |

---

## Citation

If you use PRANAVA in your research, please cite:

```bibtex
@misc{pranava2026,
  title={PRANAVA: Prompt-driven Route Generation for Autonomous Navigation of Aerial Vehicles using Generative AI},
  author={Varun Vivek Pai},
  year={2026}
}
```

---
