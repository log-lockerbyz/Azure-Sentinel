import logging
import os
from datetime import datetime, timezone, timedelta

import azure.functions as func
from connections.sentinel import SentinelConnector
from connections.zerofox import ZeroFoxClient


def main(mytimer: func.TimerRequest) -> None:
    now = datetime.now(timezone.utc)
    utc_timestamp = (
        now.isoformat()
    )

    if mytimer.past_due:
        logging.info("The timer is past due!")

    customer_id = os.environ.get("WorkspaceID")
    shared_key = os.environ.get("WorkspaceKey")

    query_from = max(
        mytimer.schedule_status["Last"], (now - timedelta(days=1)).isoformat())

    zf_client = get_zf_client()

    results = get_cti_phishing(
        zf_client, scanned_after=query_from
    )

    logging.debug("Trigger function retrieved results")

    # The log type is the name of the event that is being submitted
    log_type = "ZeroFox_CTI_phishing"

    sentinel_client = SentinelConnector(
        customer_id=customer_id, shared_key=shared_key, log_type=log_type
    )

    for result in results:
        sentinel_client.send(result)

    logging.info("Python timer trigger function ran at %s", utc_timestamp)


def get_zf_client():
    user = os.environ.get("ZeroFoxUsername")
    token = os.environ.get("ZeroFoxToken")
    return ZeroFoxClient(user, token)


def get_cti_phishing(client: ZeroFoxClient, scanned_after):
    url_suffix = "phishing/"
    params = dict(scanned_after=scanned_after)
    return client.cti_request(
        "GET",
        url_suffix,
        params=params,
    )
