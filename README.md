# Team Solar Sprinters – [App Name]
A dating/matchmaking site specifically for NYU students (Mobile-First Design Focus)

## Product vision statement
*A student-focused matchmaking platform that helps NYU students discover compatible peers, connect over shared interests, and build meaningful relationships.*

## Links
- [Sprint 1 Board](https://github.com/your-org/your-repo/projects/X)
- [Sprint 2 Board](https://github.com/your-org/your-repo/projects/Y)

## User stories
[Issues (User Stories)](https://github.com/swe-students-spring2026/2-web-app-solar_sprinters/issues)

## Steps necessary to run the software

### 1. clone and enter the repository
```shell
git clone https://github.com/swe-students-spring2026/2-web-app-solar_sprinters.git

cd 2-web-app-solar_sprinters/

```
### 2. create local env file
```shell
# copies an example env to your local env
cp example-env.txt .env
```
now go into the env file, and edit the following lines:
1. inside the second line, change the <db_username> and <db_password> to the actual username/password we provided:
`username: nyu-app-user
password: wxPwopSb5FrtSdG3`

2. run the command listed in line 7 in your terminal shell:
`python -c "import secrets; print(secrets.token_hex(32))"`

   This will generate a secret key in your shell editor. Paste it in after the SECRET_KEY.

Don't share any of the contents inside the env file. Make sure it's included in the gitignore and not pushed. 

### 3. create and activate virtual environment
```shell
python -m venv .venv
   #WINDOWS POWERSHELL:
   .venv\Scripts\Activate.ps1
   #WINDOWS CMD:
   .venv\Scripts\activate.bat
   #MAC/LINUX:
   source .venv/bin/activate
```

### 4. Install dependencies and run
   ```shell
   pip install -r requirements.txt
   cd back-end/
   flask run
   ```

### 5. Open browser and go to:
   ```shell
   http://127.0.0.1:5000
   ```

### 6. upon completion:
quit flask and venv:
```shell
deactivate
```

## Task boards
https://github.com/orgs/swe-students-spring2026/projects/5/views/1?filterQuery=