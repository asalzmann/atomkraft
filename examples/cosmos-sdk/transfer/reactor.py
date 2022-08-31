import logging
import time

from modelator.pytest.decorators import step
from terra_sdk.client.lcd import LCDClient
from terra_sdk.client.lcd.api.tx import CreateTxOptions
from terra_sdk.core import Coin, Coins
from terra_sdk.core.bank import MsgSend
from terra_sdk.core.fee import Fee
from terra_sdk.key.mnemonic import MnemonicKey


@step("Init")
def init(testnet, action):
    logging.info("Step: Init")
    testnet.n_account = action["value"]["n_wallet"]
    testnet.verbose = True

    testnet.oneshot()
    time.sleep(10)

    logging.info("Status: Testnet launched\n")


@step("Transfer")
def transfer(testnet, action):
    logging.info("Step: Transfer")

    rest_endpoint = testnet.get_validator_port(0, "lcd")
    lcdclient = LCDClient(
        url=rest_endpoint,
        chain_id=testnet.chain_id,
        gas_prices=f"10{testnet.denom}",
        gas_adjustment=0.1,
    )

    sender_id = action["value"]["sender"]
    receiver_id = action["value"]["receiver"]
    amount = action["value"]["amount"]

    sender = testnet.accounts[sender_id].address(testnet.prefix)
    receiver = testnet.accounts[receiver_id].address(testnet.prefix)

    sender_wallet = lcdclient.wallet(
        MnemonicKey(
            mnemonic=testnet.accounts[sender_id].mnemonic,
            coin_type=testnet.coin_type,
            prefix=testnet.prefix,
        )
    )

    msg = MsgSend(sender, receiver, Coins([Coin(testnet.denom, amount)]))

    tx = sender_wallet.create_and_sign_tx(
        CreateTxOptions(
            msgs=[msg], fee=Fee(20000000, Coins([Coin(testnet.denom, 2000000)]))
        )
    )

    result = lcdclient.tx.broadcast(tx)

    logging.info(f"\tSender:    {msg.from_address}")
    logging.info(f"\tReceiver:  {msg.to_address}")
    logging.info(f"\tAmount:    {msg.amount}")

    if result.code == 0:
        logging.info("Status: Successful\n")
    else:
        logging.info("Status: Error")
        logging.info(f"\tcode: {result.code}")
        logging.info(f"\tlog:  {result.raw_log}\n")

    logging.debug(f"[MSG] {msg}")
    logging.debug(f"[RES] {result}")

    time.sleep(2)
