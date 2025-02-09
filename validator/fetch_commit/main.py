import time
import sys
import logging
from typing import Any, cast
import bittensor as bt
from bittensor.core.extrinsics.serving import get_metadata
import redis
import json
from collections import defaultdict
import utils

import logging
from colorama import init, Fore

# Initialize colorama
init(autoreset=True)


# Custom logging formatter to add colors and emojis
class ColoredFormatter(logging.Formatter):
    COLORS = {
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.MAGENTA,
    }

    def format(self, record):
        log_level = record.levelname
        color = self.COLORS.get(log_level, Fore.WHITE)
        message = super().format(record)
        return f"{color} {message}"


# Configure logging with color logging for console output
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),  # Outputs to the console
        logging.FileHandler("commit_fetching.log", mode="w"),  # Logs to a file
    ],
)

# Get the root logger
logger = logging.getLogger()

# Set custom colored formatter for the console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(
    ColoredFormatter("%(asctime)s - %(levelname)s - %(message)s")
)
logger.handlers[0] = (
    console_handler  # Replace the default stream handler with our colored one
)


previous_commits = defaultdict(dict)


def fetch_commits(config: bt.config, redis_queue: redis.Redis):
    """
    Async task to fetch commits and put them into the commit queue.

    Args:
        config (bt.config): Configuration object.
    """
    try:
        wallet = bt.wallet(config=config)
        subtensor = bt.subtensor(config=config)
        metagraph: bt.metagraph = subtensor.metagraph(config.netuid)

        # Ensure the wallet is registered
        try:
            hotkey, uid = utils.assert_registered(wallet, metagraph)
            logging.info(f"Hotkey {hotkey} is registered with UID {uid}.")
        except ValueError as e:
            logging.error(
                f"Hotkey {wallet.hotkey.ss58_address} is not registered on subnet {config.netuid}."
            )
            return

        try:
            utils.assert_sufficient_stake(wallet, metagraph)
            logging.info(
                f"Validator (uid: {uid}) has sufficient stake to set weights on the subnet."
            )
        except ValueError as e:
            logging.error(
                f"Hotkey ({wallet.hotkey.ss58_address}) (uid: {uid}) does not have sufficient stake to set weights on the subnet."
            )
            return

        logging.info("Initiating the commit fetching process...")

        while True:
            logging.info("Fetching commits...")
            for uid in metagraph.uids:
                try:
                    # Fetch the current commit
                    current_commit = subtensor.get_commitment(
                        netuid=config.netuid, uid=uid
                    )
                    # Check if commit has changed
                    if current_commit and current_commit != (
                        previous_commits.get(uid)[0]
                        if previous_commits.get(uid)
                        else None
                    ):
                        hotkey = metagraph.hotkeys[uid]
                        metadata = cast(
                            dict[str, Any],
                            get_metadata(subtensor, metagraph.netuid, hotkey),
                        )
                        commit_block = metadata["block"]
                        data = {
                            "uid": int(uid),
                            "current_commit": current_commit,
                            "commit_block": commit_block,
                        }
                        redis_queue.rpush("commit_queue", json.dumps(data))
                        logging.info(f"Pushed commit data to Redis: {data}")
                        previous_commits[uid] = (current_commit, commit_block)
                    # If commit is not changed in one day, giving punishment
                    elif (
                        current_commit
                        and (
                            subtensor.get_current_block()
                            - (
                                previous_commits.get(uid)[1]
                                if previous_commits.get(uid)
                                else None
                            )
                        )
                        > 7200
                    ):
                        logging.warning(
                            f"Commit for UID {uid} has not changed in over a day, updating score."
                        )
                        previous_commits[uid] = (
                            current_commit,
                            subtensor.get_current_block(),
                        )
                        raw_score = redis_queue.hget("scores", int(uid))
                        current_score = json.loads(raw_score) if raw_score else 0
                        updated_score = current_score * 0.8
                        redis_queue.hset("scores", int(uid), json.dumps(updated_score))
                    else:
                        logging.warning(
                            f"No new commit for UID {uid} or commit unchanged for a day, skipping."
                        )
                        continue
                except Exception as e:
                    logging.error(
                        f"Encountered an error while fetching commit for UID {uid}: {e}. Skipping this UID.",
                        exc_info=True,
                    )

            # Sleep for the interval defined in config
            logging.info("Pausing for 5 minutes before the next commit fetch cycle.")
            time.sleep(5 * 60)

    except Exception as e:
        logging.error(
            f"Unable to fetch commits at this time. Please verify the configuration and try again. Error: {e}",
            exc_info=True,
        )

        sys.exit(1)


def main():

    try:
        redis_queue = redis.Redis(host="localhost", port=6379, db=0)
        config = utils.get_config()
        logging.info(config)
        fetch_commits(config, redis_queue)

    except KeyboardInterrupt:
        print("🔴 Fetch-commit Process interrupted by user")


if __name__ == "__main__":

    main()
