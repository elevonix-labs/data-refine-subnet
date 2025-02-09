# Validator

This script is designed to commit datasets to the Bittensor subtensor chain. It initializes and parses command-line arguments, sets up the wallet and subtensor, and retrieves and processes datasets from the Bittensor metagraph.

## System and Hardware Requirements

### 1. **Hardware Requirements**

#### Recommended Hardware

- **CPU**: AMD Ryzen 7 or Ryzen 9
- **RAM**: 64 GB or higher
- **Storage**: 250 GB free disk space for dataset storage and processing
- **GPU**:
  - **Minimum Model**: NVIDIA RTX 3070 or equivalent
  - **Minimum Memory**: 8 GB of VRAM
  - **Minimum Count**: 1
  - **Recommended Model**: NVIDIA RTX 3080/3090 or NVIDIA A40
  - **Recommended Memory**: Minimum 8 GB of VRAM
  - **Recommended Count**: 4+ (for optimal performance with larger datasets)

### 2. **Software Requirements**

- **Operating System** (Ubuntu 22.04.04+ recommended)
- **Python Version** (Python 3.10 + recommended)
- **Poetry**: For managing project dependencies and running scripts. (Refer to the [Installation Guide](#installing-poetry))
- **Git**: Version control system for managing code repositories.

## Install Dependencies

### Installing Poetry

#### First, make sure you have Poetry installed. If not, install it using

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

This installation script should automatically add Poetry to your PATH. If the installation was successful, try running:

```bash
poetry --version
```

#### Add Poetry to Your PATH Manually

- First, locate the Poetry binary:

```bash
echo "$HOME/.local/bin/poetry"
```

- Add the Poetry binary directory to your PATH by editing your shell configuration file `nano ~/.bashrc`, `~/.zshrc`, or `~/.profile`

```bash
export PATH="$HOME/.local/bin:$PATH"
```

- After adding it to your PATH, apply the changes:

```bash
source ~/.bashrc
```

Now, you should be able to run:

```bash
poetry --version
```

### Installing PM2 (optional)

```bash
sudo apt install nodejs && npm
npm install -g pm2@latest
```

### Getting code

```bash
git clone https://github.com/elevonix-labs/finest-data-subnet.git
```

### AWS Credentials

You will need to have AWS config and credentials in the following file:

~/.aws/config

```bash
[default]
region = us-west-1
output = json
```


~/.aws/credentials

```bash
[default]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
```
Or you can add it in .env file
Plz check .env.sample file for more details.

### Adding .env file

```bash
cp .env.sample .env
```

### Adding API_URL

You need to add API_URL in .env file.

```bash
API_URL=https://finest-data-api.elevonix.io/api
```

### Adding WANDB_API_KEY

You need to add WANDB_API_KEY in .env file.

```bash
WANDB_API_KEY=YOUR_WANDB_API_KEY
```

### Installing Dependencies

Ensure you have the required dependencies installed. You can use the following command to install them:

```bash
cd validator
./setup_environments.sh

```

### Running  Redis
We should have redis running on the machine.

If you didn't install sudo, install it first.

```bash
sudo apt update
sudo apt install sudo
```

Install redis

```bash
sudo apt install redis-server

sudo service redis-server start

```
Check if redis is running

```bash
redis-cli ping
```


## Running Validator

### 1. Creating Bittensor wallet.
Make sure you have the necessary environment setup. You should have a Bittensor wallet and access to the Bittensor subtensor chain.

You can active poetry venv for creating wallet.

```bash
source fetch_commit/.venv/bin/activate
```

- Creating a coldkey using `btcli`

`btcli wallet new_coldkey --wallet.name <my_coldkey>`
For example,
`btcli wallet new_coldkey --wallet.name test-coldkey`

- Creating a hotkey using `btcli`

`btcli wallet new_hotkey --wallet.name <my_coldkey> --wallet.hotkey <my_hotkey>`
For example,
`btcli wallet new_hotkey --wallet.name test-coldkey --wallet.hotkey test-hotkey`

You can check more about it in [bittensor docs](https://docs.bittensor.com/working-with-keys)


### 2. Running the Script

#### Without auto-updates

You can run the script using the following command:

- Mainnet
```bash
poetry run python main.py --wallet_name your_wallet_name --wallet_hotkey wallet_hotkey [--world_size gpu_count]
```

Example

```bash
poetry run python main.py --wallet_name validator --wallet_hotkey default --world_size 1
```
Or run with pm2
```bash
pm2 start main.py --name validator --interpreter .venv/bin/python -- --wallet_name validator --wallet_hotkey default --world_size 1
```

- Testnet
```bash
poetry run python main.py --netuid <netuid> --subtensor_network test --wallet_name your_wallet_name --wallet_hotkey wallet_hotkey [--world_size gpu_count]
```

Example

```bash
poetry run python main.py --netuid 250 --subtensor_network test --wallet_name test-validator --wallet_hotkey h1 --world_size 1
```
Or run with pm2
```bash
pm2 start main.py --name test-validator --interpreter .venv/bin/python -- --netuid 250 --subtensor_network test --wallet_name test-validator --wallet_hotkey h1 --world_size 1
```


- Custom
```bash
poetry run python main.py --wallet_name your_wallet_name --wallet_hotkey wallet_hotkey --subtensor_chain_endpoint address [--world_size gpu_count]
```

Example

```bash
poetry run python main.py --wallet_name test-validator --wallet_hotkey h1 --subtensor_chain_endpoint ws://localhost:9946 --world_size 1
```
Or run with pm2
```bash
pm2 start main.py --name validator --interpreter .venv/bin/python -- --wallet_name test-validator --wallet_hotkey h1 --subtensor_chain_endpoint ws://localhost:9946 --world_size 1
```


#### With auto-updates

1. For running with auto-updates, you should run it in project root directory, now you are in `validator` directory, so can run this command `cd ..`
2. Make sure you're using the main branch: `git checkout main.`

- Mainnet
```bash
pm2 start --name sn63-validator-updater --interpreter python3 scripts/start_validator.py -- --pm2_name sn63-validator --wallet_name validator --wallet_hotkey h1 --world_size 1
```

- Testnet
```bash
pm2 start --name sn63-validator-updater --interpreter python3 scripts/start_validator.py -- --pm2_name sn63-validator --netuid 250 --subtensor_network test --wallet_name test-validator --wallet_hotkey h1 --world_size 1
```

- Custom
```bash
pm2 start --name sn63-validator-updater --interpreter python3 scripts/start_validator.py -- --pm2_name sn63-validator --wallet_name test-validator --wallet_hotkey h1 --subtensor_chain_endpoint ws://localhost:9946 --world_size 1
```




**Explanation of the arguments:**
- **--netuid**, **--wallet_name**, **--wallet_hotkey**, **--subtensor_network**: These arguments are used to specify the wallet name, hotkey, subtensor network of bittensor network. Plz check (bittensor docs)[https://docs.bittensor.com/] for more details.
- **--world_size**: This argument sets the world_size. In the context of the script, it is used to determine the number of GPUs to use, as seen in the get_world_size function. We set 1 as default.
