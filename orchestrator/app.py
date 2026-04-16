from flask import Flask, request, jsonify
import docker
import os
import threading
import time
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

app = Flask(__name__)

client = docker.from_env()
running_containers = {}  # Track containers: {challenge_name: {'container': obj, 'port': int, 'start_time': time}}

scheduler = BackgroundScheduler()
scheduler.start()

def stop_container(challenge_name):
    if challenge_name in running_containers:
        container = running_containers[challenge_name]['container']
        container.stop()
        container.remove()
        del running_containers[challenge_name]
        print(f"Stopped and removed container for {challenge_name}")

#This will only initialize the image, not start the container
@app.route('/initialize_challenge', methods=['POST'])
def initialize_challenge():
    data = request.json
    challenge_name = data.get('challenge_name')
    if not challenge_name:
        return jsonify({'error': 'challenge_name required'}), 400

    image_name = f"ctf-{challenge_name}:latest"
    if image_name in [img.tags[0] for img in client.images.list() if img.tags]:
        return jsonify({'message': f'Challenge {challenge_name} already initialized', 'challenge_initialized': True})
    else:
        dir_path = f"/storage/{challenge_name}"
        dockerfile_rel = "docker/Dockerfile"

        docker_file = f"""FROM python:3.11-slim

WORKDIR /challenge
COPY resources /challenge

EXPOSE 80
CMD [\"python3\", \"-m\", \"http.server\", \"80\"]"""

        dockerfile_path = os.path.join(dir_path, dockerfile_rel)
        if not os.path.exists(dockerfile_path):
            with open(dockerfile_path, "x") as f:
                f.write(docker_file)

        #problem jest tutaj że nie chce się zbudować
        try:
            print(f"Building image from context {dir_path} using Dockerfile {dockerfile_rel}")
            client.images.build(path=dir_path, dockerfile=dockerfile_rel, tag=image_name)
            print(f"Successfully built {image_name}")
        except Exception as e:
            print(f"Build failed: {e}")
            return jsonify({'error': f'Failed to build image: {str(e)}'}), 500
        
        return jsonify({'message': f'Challenge {challenge_name} initialized', 'challenge_initialized': True})

#this will start the container and return the port it's running on
@app.route('/start_challenge', methods=['POST'])
def start_challenge():
    data = request.json
    challenge_name = data.get('challenge_name')
    if not challenge_name:
        return jsonify({'error': 'challenge_name required'}), 400

    # Check if already running
    if challenge_name in running_containers:
        return jsonify({'port': running_containers[challenge_name]['port']})

    image_name = f"ctf-{challenge_name}:latest"

    try:
        client.images.get(image_name)
    except docker.errors.ImageNotFound:
        return jsonify({'error': 'Challenge image not found'}), 404
    
    container = client.containers.run(image_name, detach=True, ports={'80/tcp': None})
    container.reload()
    port = container.attrs['NetworkSettings']['Ports']['80/tcp'][0]['HostPort']
    running_containers[challenge_name] = {'container': container, 'port': port, 'start_time': time.time()}
    return jsonify({'port': port, 'container_id': container.id})

@app.route('/stop_challenge', methods=['POST'])
def stop_challenge():
    data = request.json
    challenge_name = data.get('challenge_name')
    if challenge_name in running_containers:
        stop_container(challenge_name)
        return jsonify({'message': f'Stopped {challenge_name}'})
    return jsonify({'error': 'Challenge not running'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)