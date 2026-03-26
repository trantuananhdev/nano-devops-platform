param(
  [string]$Input = "samples/raw/session_demo_002.json"
)

$ErrorActionPreference = "Stop"

python -m pip install -r requirements.txt
python -m pip install -e .

python -m teencare_ai --input $Input

