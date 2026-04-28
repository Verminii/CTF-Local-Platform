from flask import Flask, request, jsonify
import docker
import os
import re
import threading
import time
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

app = Flask(__name__)

client = docker.from_env()
running_containers = {}  # Track containers: {user_challenge_key: {'challenge_name': str, 'user': str, 'container': obj, 'port': int, 'start_time': time}}

scheduler = BackgroundScheduler()
scheduler.start()


def sanitize_name(value):
    return re.sub(r'[^a-zA-Z0-9_.-]', '_', str(value)).strip('_')[:128]


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
    user = data.get('user')

    print('start_challenge request', {'challenge_name': challenge_name, 'user': user})

    if not challenge_name:
        return jsonify({'error': 'challenge_name required'}), 400
    if not user:
        return jsonify({'error': 'user required'}), 400

    sanitized_challenge = sanitize_name(challenge_name)
    sanitized_user = sanitize_name(user)
    container_key = f"{sanitized_challenge}:{sanitized_user}"
    image_name = f"ctf-{sanitized_challenge}:latest"
    container_name = f"ctf-{sanitized_challenge}-{sanitized_user}"

    print('resolved names', {
        'sanitized_challenge': sanitized_challenge,
        'sanitized_user': sanitized_user,
        'container_key': container_key,
        'image_name': image_name,
        'container_name': container_name,
    })

    if container_key in running_containers:
        existing = running_containers[container_key]
        print('container already running:', existing['container'].id, 'port=', existing['port'])
        return jsonify({
            'port': existing['port'],
            'container_id': existing['container'].id,
            'container_name': existing['container'].name,
            'challenge_name': challenge_name,
            'user': user,
            'sanitized_challenge': sanitized_challenge,
            'sanitized_user': sanitized_user,
        })

    try:
        client.images.get(image_name)
    except docker.errors.ImageNotFound:
        print('image not found:', image_name)
        return jsonify({'error': 'Challenge image not found', 'image_name': image_name}), 404

    try:
        existing = client.containers.get(container_name)
        print('existing container found with same name, removing:', existing.id)
        existing.stop()
        existing.remove()
    except docker.errors.NotFound:
        pass
    except Exception as e:
        print('error removing existing container', e)

    try:
        container = client.containers.run(
            image_name,
            detach=True,
            ports={'80/tcp': None},
            name=container_name
        )
    except Exception as e:
        print('error starting container', e)
        return jsonify({'error': 'Failed to start container', 'message': str(e), 'container_name': container_name}), 500

    container.reload()
    port = container.attrs['NetworkSettings']['Ports']['80/tcp'][0]['HostPort']
    running_containers[container_key] = {
        'challenge_name': challenge_name,
        'user': user,
        'container': container,
        'port': port,
        'start_time': time.time()
    }
    print('started container', {'id': container.id, 'port': port, 'name': container.name})
    return jsonify({
        'port': port,
        'container_id': container.id,
        'container_name': container.name,
        'challenge_name': challenge_name,
        'user': user,
        'sanitized_challenge': sanitized_challenge,
        'sanitized_user': sanitized_user,
    })

@app.route('/stop_challenge', methods=['POST'])
def stop_challenge():
    data = request.json
    challenge_name = data.get('challenge_name')
    user = data.get('user')

    if not challenge_name:
        return jsonify({'error': 'challenge_name required'}), 400

    container_key = f"{challenge_name}:{user}" if user else challenge_name
    if container_key in running_containers:
        stop_container(container_key)
        return jsonify({'message': f'Stopped {challenge_name} for user {user or "unknown"}'})
    return jsonify({'error': 'Challenge not running'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)