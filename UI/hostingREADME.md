## Details about hosting models on local servers and accessing them via API for a working UI

Date created: June 4, 2025

### Installation
* Since we don't have sudo access on our servers, we need to manually fetch the required packages.
* Get these packages from their respective resources - 
    * **ollama**
        * follow the instructions at [this link](https://github.com/ollama/ollama/blob/main/docs/linux.md). 
        * In case that doesn't work, do ```curl -L https://ollama.com/download/ollama-linux-amd64.tgz```.
        * You'll interact with the file ```./bin/ollama```, as we don't have sudo access to install it globally.
    * **ngrok**
        * create an account at [ngrok](https://ngrok.com/) to obtain the auth token.
        * Follow the instructions at [this link](https://ngrok.com/downloads/linux?tab=download) to install ngrok.
        * In case that doesn't work, then wget [this link](https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz)
        * You'll interact with the obtained file ```ngrok```, as we don't have sudo access to install it globally.
        * Configure the auth token by running ```./ngrok config add-authtoken <your_auth_token>```.
    * pip install ```flask```

### Setting up the configuration
* As models take a lot of space, store them in a persistent disk. To do that, set up the environment variable ```export OLLAMA_MODELS=/mnt/your/path```.
* To ensure that ollama only uses specified GPUs, set the environment variable ```export OLLAMA_VISIBLE_DEVICES=XXX```.
* You need to do this for every new terminal session, or you can add these lines to your ```~/.bashrc``` file.

### Running the server
* Start the ollama server by running the command ```ollama serve&```. This will start the server in the background.
    * In case you want to terminate the server, then find the pid using ```ps aux | grep ollama```, and then kill it using ```kill -9 <pid>```.
* After starting the server, you need to pull the models you want to use. For example, to pull the mistral-small model, run ```./bin/ollama pull mistral-small```.
* To test that it is working as expected, run this test command:
    ```bash
    curl -X POST http://localhost:11434/api/generate \
        -H "Content-Type: application/json" \
        -d '{"model": "mistral-small:24b", "prompt": "Hello, how are you?"}'
    ```
* If you get a response, then the server is working fine.

### Setting up the API
* By default, the ollama server runs on port 11434. But since ollama doesn't allow external access, we need to use ngrok to expose the server to the internet.
* But we cannot directly use ngrok to expose the server, because ollama rejects requires that don't come from localhost. Therefore, we'll circumvent this by using a Flask server. (this is not the most recommended way, but it works. Ideally, we need to use a reverse proxy like nginx or caddy, but we don't have sudo access to install them and it's too much hassle).
* Create a file named `ollama_proxy.py` with the following content:
```python
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

@app.route('/api/generate', methods=['POST'])
def proxy_generate():
    payload = request.json
    response = requests.post("http://localhost:11434/api/generate", json=payload)
    return jsonify(response.json())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```
* Run the Flask server using the command ```python ollama_proxy.py```. This will start the server on port 5000. Make sure to run it in tmux or screen, so that it keeps running in the background.
* Now, you can use ngrok to expose the Flask server to the internet. Run the command ```./ngrok http 5000```. This will give you a public URL that you can use to access the API. This should also be done in tmux or screen, so that it keeps running in the background.
* You can now use the public URL to access the API. For example, if the public URL is `https://<YOUR_GENERATED_URL>.ngrok.io`, you can use the same test command as before, but with the public URL:
```bash
curl -X POST https://<YOUR_GENERATED_URL>.ngrok.io/api/generate \
    -H "Content-Type: application/json" \
    -d '{"model": "mistral-small:24b", "prompt": "Hello, how are you?"}'
```
* Enjoy using the API! Feel free to reach out to me if you face any issues or have any questions.