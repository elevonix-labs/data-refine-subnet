import bittensor as bt
import numpy as np
import utils
import redis
import sys
import os
import time
from utils import process_weights_for_netuid, convert_weights_and_uids_for_emit
import logging
from wandb_logger import WandbLogger
# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),  # Outputs to the console
        logging.FileHandler(
            "weight_setting.log", mode="w"
        ),  # Overwrites the log file each time
    ],
)


def set_weights(
    scores: list, config: bt.config, metagraph: bt.metagraph, subtensor: bt.subtensor
):
    """Sets weights on the blockchain based on provided scores."""

    if np.isnan(scores).any():
        logging.warning("Scores contain NaN values. Exiting weight setting.")
        return

    # Compute the norm of the scores
    norm = np.linalg.norm(scores, ord=1, axis=0, keepdims=True)

    if np.any(norm == 0) or np.isnan(norm).any():
        logging.warning("Norm is zero or NaN. Adjusting to avoid division by zero.")
        norm = np.ones_like(norm)  # Avoid division by zero or NaN

    # Compute raw_weights safely
    raw_weights = scores / norm
    logging.info(f"Raw weights: {raw_weights}")
    wallet = bt.wallet(config=config)

    try:
        processed_weight_uids, processed_weights = process_weights_for_netuid(
            uids=metagraph.uids,
            weights=raw_weights,
            netuid=config.netuid,
            subtensor=subtensor,
            metagraph=metagraph,
        )

        uint_uids, uint_weights = convert_weights_and_uids_for_emit(
            uids=processed_weight_uids, weights=processed_weights
        )
        result, msg = subtensor.set_weights(
            wallet=wallet,
            netuid=config.netuid,
            uids=uint_uids,
            weights=uint_weights,
            wait_for_finalization=False,
            wait_for_inclusion=False,
        )

        if result:
            logging.info("🚀 set_weights on chain successfully!")
            return True
        else:
            logging.error(f"set_weights failed: {msg}")
            return False

    except Exception as e:
        logging.error(f"An error occurred during weight setting: {e}", exc_info=True)
        return False


def main(config: bt.config, subtensor: bt.subtensor):
    """Main loop to periodically set weights."""
    try:
        wandb_api_key = os.getenv("WANDB_API_KEY")
        if wandb_api_key is None:
            logging.error("🔴 WANDB_API_KEY is not set")
            sys.exit(1)
    except Exception as e:
        logging.error(f"🔴 An error occurred while logging in to Wandb: {e}", exc_info=True)
        sys.exit(1)

    wandb_logger = WandbLogger()
    redis_queue = redis.Redis(host="localhost", port=6379, db=0)

    saved_scores = wandb_logger.get_all_scores()

    if saved_scores:
        logging.info("Successfully fetched scores from Wandb.")
        redis_queue.hset('scores', mapping=saved_scores)

    logging.info("Started main loop to periodically set weights.")
    try:
        while True:
            try:
                if subtensor.get_current_block() % 100 == 0:
                    metagraph: bt.metagraph = subtensor.metagraph(config.netuid)
                    raw_scores = redis_queue.hgetall("scores")

                    scores = [
                        float(raw_scores.get(str(uid).encode('utf-8'), b"0").decode('utf-8'))
                        for uid in metagraph.uids
                    ]

                    logging.info(f"Setting weights for {len(scores)} UIDs...")
                    is_set = set_weights(scores, config, metagraph, subtensor)

                    if is_set:
                        for i, value in enumerate(scores):
                            wandb_logger.log_wandb({"uid": i, "score": value})

                    logging.info("Waiting for next cycle...")
                    time.sleep(10)

            except Exception as e:
                logging.error(f"An error occurred in the main loop: {e}", exc_info=True)
                sys.exit(1)

    except KeyboardInterrupt:
        print("🔴 Weight-setter Process interrupted by user.")
    except Exception as e:
        print(f"{e}")
        sys.exit(1)


if __name__ == "__main__":

    logging.info("Initializing the process...")

    config = utils.get_config()
    subtensor = bt.subtensor(config=config)
    main(config, subtensor)
