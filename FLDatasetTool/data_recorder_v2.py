import carla
import numpy as np
import cv2
import asyncio
import socketio
import random
import time

# Initialize Socket.IO client
sio = socketio.AsyncClient()

@sio.event
async def connect():
    print("Connected to Socket.IO server")

@sio.event
async def disconnect():
    print("Disconnected from Socket.IO server")

async def send_camera_data(data):
    print("send camera data", data[1], data[2])
    await sio.emit("carla_image", data)
    print("data sent")


sensor_tick = '0.2'

# Connect to the CARLA server
client = carla.Client('localhost', 2000)
client.set_timeout(10.0)
# Get the world and blueprint library
client.reload_world()
tm = client.get_trafficmanager(8000)
world = client.load_world("Town02")
settings = world.get_settings()
settings.fixed_delta_seconds = 0.025
settings.max_substeps = 16
world.apply_settings(settings)
settings = world.get_settings()
print(settings)
blueprint_library = world.get_blueprint_library()

# Spawn the ego vehicle (Tesla Model 3)
vehicle_bp = blueprint_library.filter('vehicle.tesla.model3*')[0]
spawn_point = world.get_map().get_spawn_points()[0]
vehicle = world.spawn_actor(vehicle_bp, spawn_point)

# Create and attach two camera sensors
camera_bp_1 = blueprint_library.find('sensor.camera.rgb')
camera_bp_1.set_attribute('image_size_x', '1242')
camera_bp_1.set_attribute('image_size_y', '375')
camera_bp_1.set_attribute('fov', '90')
camera_bp_1.set_attribute('sensor_tick', sensor_tick)  # Set frequency to 0.1 seconds

camera_transform_1 = carla.Transform(carla.Location(x=2.0, y=0.06, z=1.65))
camera_1 = world.spawn_actor(camera_bp_1, camera_transform_1, attach_to=vehicle)

camera_bp_2 = blueprint_library.find('sensor.camera.rgb')
camera_bp_2.set_attribute('image_size_x', '1242')
camera_bp_2.set_attribute('image_size_y', '375')
camera_bp_2.set_attribute('fov', '90')
camera_bp_2.set_attribute('sensor_tick', sensor_tick)  # Set frequency to 0.1 seconds

camera_transform_2 = carla.Transform(carla.Location(x=2.0, y=-0.48, z=1.65))
camera_2 = world.spawn_actor(camera_bp_2, camera_transform_2, attach_to=vehicle)

# Add 20 other vehicles to the road
spawn_points = world.get_map().get_spawn_points()
random.shuffle(spawn_points)
number_of_vehicles = min(20, len(spawn_points) - 1)

for i in range(number_of_vehicles):
    vehicle_bp = random.choice(blueprint_library.filter('vehicle.*'))
    spawn_point = spawn_points[i + 1]  # Avoid ego vehicle spawn point
    
    npc_vehicle = world.try_spawn_actor(vehicle_bp, spawn_point)
    if npc_vehicle:
      npc_vehicle.set_autopilot(True, tm.get_port())

vehicle.set_autopilot(True, tm.get_port())


# Configure traffic lights
actor_list = world.get_actors()
for actor in actor_list:
    if isinstance(actor, carla.TrafficLight):
        actor.set_red_time(2.0)
        actor.set_green_time(0.01)
        actor.set_yellow_time(2.0)


client.start_recorder(f'./raw_data/record_{time.time()}/carla_raw_record.log', True)


def process_image(image, name):
    # Convert CARLA image to a format that can be sent via Socket.IO
    array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
    array = np.reshape(array, (image.height, image.width, 4))
    image_np = array[:, :, :3]
    _, img_encoded = cv2.imencode('.png', image_np)
    img_bytes = img_encoded.tobytes()

    with open("./calibration","rb") as f:
      with open(f"./{name}.png", "rb") as im:

      # Schedule sending image data to the Socket.IO server
        asyncio.run(send_camera_data((im.read(), name ,image.frame, f.read())))
      # res = asyncio.run(send_camera_data(("asd", image.frame)), debug=True)

async def main():
    await sio.connect('http://10.1.65.52:30005', transports=['websocket'])
    print(sio.transport())
    # Set the callback for camera sensor
    camera_1.listen(lambda image: process_image(image, "image_2"))
    camera_2.listen(lambda image: process_image(image, "image_3"))
    while True:
      await asyncio.sleep(0.05)
    

# Run the Socket.IO client
if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        client.stop_recorder()
        camera_1.destroy()
        camera_2.destroy()
        vehicle.destroy()
        client.apply_batch([carla.command.DestroyActor(x) for x in world.get_actors() if x.id != vehicle.id])
        client.reload_world()

