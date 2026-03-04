# Team Solar Sprinters – [NYU Match]
A dating/matchmaking site specifically for NYU students (Mobile-First Design Focus)

## Product vision statement
*A student-focused matchmaking platform that helps NYU students discover compatible peers, connect over shared interests, and build meaningful relationships.*

## Task Boards
- [Sprint 1 Board](https://github.com/orgs/swe-students-spring2026/projects/5/views/1?filterQuery=)
- [Sprint 2 Board](https://github.com/orgs/swe-students-spring2026/projects/66)

## User stories
[Issues (User Stories)](https://github.com/swe-students-spring2026/2-web-app-solar_sprinters/issues)

## Wireframe
[NYU Match Wireframe](https://www.figma.com/proto/hMXmgcV3I7VbQSex4dzy0N/solar_sprinters-final-design?node-id=1-3&t=ufsJ5KvcjBhZJNsj-0&scaling=scale-down&content-scaling=fixed&page-id=0%3A1&starting-point-node-id=1%3A3)

## Steps necessary to run the software

### 1. clone and enter the repository
```bash
git clone https://github.com/swe-students-spring2026/2-web-app-solar_sprinters.git

cd 2-web-app-solar_sprinters/

```
### 2. create local env file
```bash
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

_Don't share any of the contents inside the env file. Make sure it's included in the gitignore and not pushed._

### 3. create and activate pipenv
```bash
# from the project root directory:
pip install pipenv
pipenv install
# activate:
pipenv shell
```
note that if the above doesn't work, you can also try:
```bash
python3 -m pip install pipenv
python3 -m pipenv install
python3 -m pipenv shell
```

### 4. run
   ```bash
   cd backend/
   flask run
   ```

### 5. Open browser and go to
   http://127.0.0.1:5000

### 6. upon completion:
exit pipenv shell:
```shell
# stop flask
^C
# exit pipenv
exit
```