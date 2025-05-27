# BenBox

**BenBox** is an Agent AI app utilizing [MCP](https://modelcontextprotocol.io/introduction)
tools with Angular mobile and Phoenix desktop app.

[Read the project summary](PROJECT.md).

**Why MCP?**

MCP server can now be some running process that agents (clients) connect to,
use, and disconnect from whenever and wherever they want. In other words,
an SSE-based server and clients can be decoupled processes
(potentially even, on decoupled nodes). This is different and better fits
"cloud-native" use-cases compared to the STDIO-based pattern where the client
itself spawns the server as a subprocess.

**Features:**
- Azure OpenAI agent integration with remote MCP tools
- Seamless connection to remote MCP services via OpenAPI
- Multi-agent communication with specialized tool access
- Secure remote tool execution without additional authentication overhead

## Setup

Install the required packages and the MCP server and client:

```bash
# Installing Node.js on Linux
sudo apt install nodejs npm cocoapods

# Installing Node.js on Mac
brew install nodejs npm cocoapods

# Installing mcp
conda install -c conda-forge mcp 

# Cloning the repo
git clone https://github.com/DrBenjamin/BenBox
```

Running the MCP server and Streamlit client app:

```bash
# Creating a conda environment using the environment.yml file
conda env create -f environment.yml

# Activating the conda environment
conda activate benbox

# Installing the required mcp package
python -m pip install "mcp[cli]"

# 1. Running the MCP dev server
mcp dev src/server.py

# 2. Running the MCP server
python src/server.py

# 3. Running the Streamlit app
python -m streamlit run app.py

# or the run script
sudo chmod 755 run.sh
./run.sh
lsof -i :6274
lsof -i :8080
lsof -i :8501
```

### Setup of Azure

To configure the Azure OpenAI API, you need to install the Azure CLI and
Azure Dev CLI. Use the following commands to install them:

```bash
# Installing Azure CLI and Azure Dev CLI
# Azure Cli on Mac
brew tap azure/azd && brew install azd && brew install azure-cli

# Azure Cli on Linux
apt-get install -y azure-cli

# Download and run the install script for Azure Developer CLI
curl -fsSL https://aka.ms/install-azd.sh | bash

# Logging in to Azure
az login
# or on remote
az login --use-device-code

# Using Azure Dev CLI
azd auth login
# or on remote
azd auth login --use-device-code
```

### Setup of MinIO

To allow public (anonymous) access to a specific bucket, use the following command:

```bash
# Setting anonymous (public) read access to a bucket
mc anonymous set download <minio-alias>/<bucket-name>
```

### Configuration

Change Streamlit configuration in `.streamlit/st.secrets.toml`:

```toml
# LLM Provider
LLM_LOCAL = "False"  # `False` for local Ollama model, `True` for OpenAI API
SNOWFLAKE = "True"  # `True` for Snowflake, `False` for PostgreSQL

# MCP API
[MCP]
MCP_URL = "http://127.0.0.1:8080"
MCP_SYSTEM_PROMPT = "<system prompt for image recognition>"
MCP_USER_PROMPT = "<user prompt for image recognition>"

# Ollama API
[OLLAMA]
OLLAMA_URL = "http://127.0.0.1:11434"
OLLAMA_MODEL = "<ollama model>" # e.g. llava or "llama3.2-vision"

# Azure OpenAI API
[AZURE_OPENAI]
AZURE_OPENAI_API_KEY = "<your-azure-openai-api-key>"
AZURE_OPENAI_ENDPOINT = "<your-azure-openai-endpoint>"
AZURE_OPENAI_MODEL = "<your-azure-openai-model>" # e.g. gpt-4.1
AZURE_OPENAI_API_VERSION = "<your-api-version>" # e.g. 2024-02-15-preview

# Configuring LLM
[LLM]
LLM_CHATBOT_NAME = "<chatbot_name>"
LLM_SYSTEM = "Please write a short answer."
LLM_SYSTEM_PLUS = "Prioritize the most relevant information from the similarity search!"
LLM_ASSISTANT = "How can I help?"
LLM_USER_EXAMPLE = "<user_example>"
LLM_ASSISTANT_EXAMPLE = "<>assistant_example>"

# Configuring Snowflake
[snowflake]
user = "<user_name>"
account = "<account_name>"
private_key_file = "<path to rsa_key.p8>"
role = "<role_name>"
warehouse = "<warehouse_name>"
database = "<database_name>"
schema = "<schema_name>"

# Configuring PostgreSQL
[psotgresql]
user = "<user_name>"
password = "<password>"
host = "<host_name>"
port = "<port_number>"
database = "<database_name>"
table = "<table_name>"

# Configuring MinIO storage
[MinIO]
endpoint = "http://127.0.0.1:9000"
bucket = "<bucket_name>"
access_key = "<access_key>"
secret_key = "<secret_key>"
```

### Ollama

To install und run the Ollama locally with a model of your choice,
use the following command:

```bash
# Running the Ollama service
systemctl start ollama. # Linux
brew services start ollama  # or Mac

# Running the model
ollama run llama3.2-vision

# Sharing the models between Ollama and LM Studio
# https://smcleod.net/2024/03/llamalink-ollama-to-lm-studio-llm-model-linker/
go install github.com/sammcj/llamalink@latest
llamalink
```

Then change the `MCP_URL` in the `.streamlit/st.secrets.toml` file to
`http://localhost:11434`.

### dbt

To install dbt, use the following command:

```bash
# Installing dbt in the conda environment
python -m pip install dbt-core dbt-snowflake

# Installing the dbt dependencies
dbt deps

# Running the dbt project
dbt run
dbt test

# Creating dbt documentation
dbt docs generate
```

Then run the following command to create the database and tables:

```bash
# Creating the database and tables
dbt run --models staging
```

### Pytest

To run the tests, use the following command:

```bash
# Running the tests
pytest -v --tb=short --disable-warnings --maxfail=1
```

## Usage

Test bytes for an image to test on MCP Inspector (running on
[http://localhost:6274/](http://localhost:6274/)) or in VS Code Copilot Chat:

```ini
"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAAWgmWQ0AAAAASUVORK5CYII="
```

or use the Streamlit app running on [http://localhost:8501](http://localhost:8501)
to upload an image and test it.

## Mobile App

The Angular app can be run using the following commands:

```bash
# Installing Angular CLI
npm install -g @angular/cli

# Installing the required packages
npm install

# Running the app
ng serve
```

The app will be available at [http://localhost:4200](http://localhost:4200).

### Building the app for mobile

To build the app for mobile, use the following commands:

```bash
# Preparing the app for mobile
npm install @capacitor/core@5.7.8 @capacitor/cli@5.7.8 --save-dev
npm install @capacitor/browser@^5 --save-dev
npm install @capacitor/ios@5.7.8 --save-dev
npm install -D typescript --save-dev
npx cap init BenBox org.benbox.imagerecog
npx cap add ios
# or after platform was already added
npx cap sync ios
cd ios/App
pod install
```

Add the following lines to the `Info.plist` file (and change the `<ip-address>` to the
IP address of the server):

```xml
<key>NSAppTransportSecurity</key>
	<dict>
		<key>NSAllowsArbitraryLoads</key>
		<true/>
		<key>NSExceptionDomains</key>
		<dict>
			<key><ip-address></key>
			<dict>
				<key>NSTemporaryExceptionAllowsInsecureHTTPLoads</key>
				<true/>
				<key>NSTemporaryExceptionMinimumTLSVersion</key>
				<string>TLSv1.1</string>
			</dict>
		</dict>
	</dict>
```

Now you can build and run the app on iOS using the following command:

```bash
# Building the app (from project root)
npm install
npm run build
npm run cap:copy
npm run cap:open:ios
```

## BenBox desktop app

Tool for organizing the files. It can be run locally or in a Docker container and
be consumed via VNC browser session.

### Setup

[Setup description](https://github.com/DrBenjamin/BenBox/blob/main/SETUP.md)

Install dependencies:

```bash
# Installing dependencies
brew install minio/stable/mc
# or on linux
sudo apt install minio-client

# Setting up the MinIO alias
mc alias set myminio http://<ip-address>:9000 minioadmin --insecure
```

### Execution

```bash
# Running the application
python BenBox.py
```

### Building

Add the following images to the `_internal/images` folder:

- icon.ico (128x128) for Windows
- icon.icns (128x128) for MacOS
- logo.png (not more than 200px either dimension) for the GUI

To build the executables, run the following command:

```bash
# Building on Windows
pyinstaller.bat

# or for MacOS & Linux
python -m PyInstaller BenBox.spec
```

### Docker

To run the application in a Docker container, use the following command:

```bash
# Cleaning up before using Docker
# Stopping all running containers
docker-compose down

# Removing all stopped containers, unused networks, images, and build cache
docker system prune -af --volumes

# Removing all dangling images
docker image prune -f

# Removing all unused Docker volumes
docker volume prune -f

# (Optional) Removing all Docker images related to BenBox
docker images | grep benbox | awk '{print $3}' | xargs docker rmi -f

# (Optional) Removing all Docker images related to streamlit or mcp
docker images | grep -E 'streamlit|mcp' | awk '{print $3}' | xargs docker rmi -f

# Using Docker to build the images
# Building the images
docker build --no-cache -t benbox-vnc .
docker build --no-cache -f Dockerfile_Streamlit -t streamlit .
docker build --no-cache -f Dockerfile_MCP -t mcp .

# Uploading MCP image to Docker Hub
docker tag mcp <username>/mcp:latest
docker push <username>/mcp:latest

# Running the containers
docker run -it --rm -p 6080:6080 benbox-vnc
docker run -it --rm -p 8501:8501 streamlit
docker run -it --rm -p 8080:8080 mcp

# Using docker-compose
# Building the images using docker-compose
docker-compose build --no-cache

# Running them in the background
docker-compose up -d

# Removing the containers
docker-compose down
```

### OS specific notes

All executables are built with PyInstaller and need to be build on the target
system.

To run the executable on MacOS, you need to allow it after the first start in the Privacy
settings.

For Linux add the icon manually to the executable.

## Misc

Some other notes:

```bash
# Creating PDF from PROJECT.md file
pandoc PROJECT.md -o PROJECT.pdf --pdf-engine=pdflatex
```
