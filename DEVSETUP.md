# DEVSETUP.md

## MongoDB and other requirements setup for solar sprinters team development

### 1. Before working, always remember to pull the latest version of main
```bash 
git checkout main
git fetch origin
git pull origin main
```

### 2. (Recommended) Create a venv
```bash
python -m venv .venv
#WINDOWS POWERSHELL
.venv\Scripts\Activate.ps1
#WINDOWS CMD
.venv\Scripts\activate.bat
#MAC/LINUX
source .venv/bin/activate
```

### 3. Install requirements.txt
```bash
pip install -r requirements.txt
```

### 4. Join MongoDB Atlas
The professor has slides for accessing MongoDB Atlas: https://knowledge.kitchen/content/courses/database-design/notes/mongodb-setup/, but you don't have to actually do this because I've already setup the cluster.
Just create an account on MongoDB Atlas; since I (Albert) already made the Atlas project, message me with your account info so I can invite you to the shared project!
NOTE: I have it set to all IPs can access (0.0.0.0/0), but it's good practice to delete this after we are done with development.

### 5. Create your .env. IMPORTANT: we do not commit this .env file to github, make sure it's in your .gitignore
Create a .env file in the same directory as your .gitignore and fill it with the information found in `example-env.txt.`
I will send the username and password info in a separate chat.

