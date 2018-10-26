export APP_NAME="main.py"
export WORKSPACE=`pwd`
# Create/Activate virtualenv
virtualenv -p /usr/bin/python3 venv
source "$WORKSPACE/venv/bin/activate"
# Install Requirements
pip3 install -r requirements.txt
