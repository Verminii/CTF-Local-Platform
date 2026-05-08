# CTF Local Platform

## 1. Overview

This platform provides a complete solution for hosting local CTF competitions, including:

- Automatically generated challenge grid
- User registration and login system
- Django + SQLite3 based backend

## 2. Getting Started

### Installation

Clone the repository:

```
git clone https://github.com/Verminii/CTF-Local-Platform.git
```

Enter the project directory and run:

```
docker compose up --build
```

The platform will start automatically and will be available at:

```
YOUR_PC_IP:8000
```

## 3. Usage

After opening the website, you can create an account and log in. Once authenticated, you will gain access to the main challenge panel, where you can browse and solve available tasks.

A **Scoreboard** page is also available in the navigation bar, allowing you to track your current ranking during the competition.

## 4. Creating Challenges

To add a new challenge, create a folder named after your challenge and place it inside:

```
backend/CTFPlatformLocal/storage/
```

All remaining setup is handled automatically by the application when the Docker instance starts.

Inside the challenge folder, the following structure is required:

- `description.txt`  
    Contains the full challenge description displayed on the challenge detail page.
- `flag/flag.txt`  
    Stores the correct flag for the challenge.
- `hints/`  
    Folder containing hint files named like:
    
    ```
    1.txt 2.txt
    ```
    
    Each hint file should contain:
    
    - First line — hint cost in points
    - Second line and below — hint content
    
    > Currently, image and file-based hints are not supported.
    
- `points.txt`  
    Single-line file containing the number of points awarded for solving the challenge.
- `short_description.txt`  
    Short preview text shown on the challenge tile. Keep it concise.
- `[OPTIONAL] docker/`  
    If your challenge requires a dedicated service or website, include a `docker` folder containing:
    - `Dockerfile`
    - All files required to build and run the challenge container
- `[OPTIONAL] resources/`  
    Place downloadable files required for solving the challenge here. They will automatically appear on the challenge detail page.
