# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0.

from awscrt import mqtt
from awsiot import mqtt_connection_builder, mqtt5_client_builder
from uuid import uuid4
import json
import os
import sys
import threading
import time

mqtt_host = os.getenv('DCF_MQTT_HOST', default='almfwrqpajske-ats.iot.us-east-1.amazonaws.com')


# Callback when connection is accidentally lost.
def on_connection_interrupted(connection, error, **kwargs):
    print("Connection interrupted. error: {}".format(error))


# Callback when an interrupted connection is re-established.
def on_connection_resumed(connection, return_code, session_present, **kwargs):
    print("Connection resumed. return_code: {} session_present: {}".format(return_code, session_present))

    if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
        print("Session did not persist. Resubscribing to existing topics...")
        resubscribe_future, _ = connection.resubscribe_existing_topics()

        # Cannot synchronously wait for resubscribe result because we're on the connection's event-loop thread,
        # evaluate result with a callback instead.
        resubscribe_future.add_done_callback(on_resubscribe_complete)


def on_resubscribe_complete(resubscribe_future):
        resubscribe_results = resubscribe_future.result()
        print("Resubscribe results: {}".format(resubscribe_results))

        for topic, qos in resubscribe_results['topics']:
            if qos is None:
                sys.exit("Server rejected resubscribe to topic: {}".format(topic))


def connect(conn):
    connect_future = conn.connect()
    connect_future.result()
    print("Established connection to MQTT!")


def mqtt_connection_from_certfiles(client_id, cert_path, private_key_path, ca_path):
    conn = mqtt_connection_builder.mtls_from_path(
            endpoint=mqtt_host,
            port=8883,
            cert_filepath=cert_path,
            pri_key_filepath=private_key_path,
            ca_filepath=ca_path,
            on_connection_interrupted=on_connection_interrupted,
            on_connection_resumed=on_connection_resumed,
            client_id=client_id,
            clean_session=False,
            keep_alive_secs=30)
    connect(conn)
    return conn


def mqtt_connection_from_certs(client_id, cert, private_key, ca):
    conn = mqtt_connection_builder.mtls_from_bytes(
            endpoint=mqtt_host,
            port=8883,
            cert_bytes=cert,
            pri_key_bytes=private_key,
            ca_bytes=ca,
            on_connection_interrupted=on_connection_interrupted,
            on_connection_resumed=on_connection_resumed,
            client_id=client_id,
            clean_session=False,
            keep_alive_secs=30)
    connect(conn)
    return conn
