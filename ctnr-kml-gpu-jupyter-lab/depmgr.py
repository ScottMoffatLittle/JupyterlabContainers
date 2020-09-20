import os
import sys
import traceback
import logging
import argparse

import requests
import zmq

DEALER_PORT = 9009
ZMQ_HEARTBEAT = 900

logger = logging.getLogger("kml-dep-mgr")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handlerC = logging.StreamHandler(sys.stdout)
handlerC.setFormatter(formatter)
logger.addHandler(handlerC)

DEFAULT_EVENT_SIG = {}


def register_event_lifecycle(api_base, credentials, event_sub_type):

    payload = {
        "event_type": "LIFECYCLE",
        "reporter_type": "INGRESS_CONTROLLER",
        "event_sub_type": event_sub_type
    }

    payload.update(DEFAULT_EVENT_SIG)

    try:
        logger.info(f"Registering lifecycle event {event_sub_type}...attempting")
        _ = requests.post(f"{api_base}/admin/events/register",
                          auth=credentials,
                          json=payload)
        logger.info(f"Registering lifecycle event {event_sub_type}...complete")

    except Exception as e:
        logger.error(e)
        logger.error(payload)
        error_type, error, tb = sys.exc_info()
        logger.error(traceback.format_tb(tb))
        traceback.print_exc(file=sys.stdout)


def register_event_metrics(api_base, credentials, seq_id=None,
                           recs_received=None, recs_relayed=None,
                           recs_inf_success=None, recs_inf_failure=None,
                           recs_inf_persisted=None, throughput_inf=None,
                           throughput_e2e=None):

    payload = {
        "event_type": "METRICS",
        "reporter_type": "INGRESS_CONTROLLER",
        "seq_id": seq_id,
        "recs_received": recs_received,
        "recs_relayed": recs_relayed,
        "recs_inf_success": recs_inf_success,
        "recs_inf_failure": recs_inf_failure,
        "recs_inf_persisted": recs_inf_persisted,
        "throughput_inf": throughput_inf,
        "throughput_e2e": throughput_e2e
    }

    payload.update(DEFAULT_EVENT_SIG)

    try:
        _ = requests.post(f"{api_base}/admin/events/register",
                          auth=credentials,
                          json=payload)

    except Exception as e:
        logger.error(e)
        logger.error(payload)
        error_type, error, tb = sys.exc_info()
        logger.error(traceback.format_tb(tb))
        traceback.print_exc(file=sys.stdout)


def main():

    try:

        parser = argparse.ArgumentParser()

        parser.add_argument('--model-dep-id',
                            help='KML Model Deployment ID', type=int,
                            required=True)
        parser.add_argument('--kml-api-base',
                            help='KML REST API base path connection string',
                            required=True)

        parser.add_argument('--dep-mgr-ip',
                            help='Deployment Manager (self) id',
                            required=True)
        parser.add_argument('--zmq-host',
                            help='Inbound ZMQ Host',
                            required=True)
        parser.add_argument('--zmq-port',
                            help='Inbound ZMQ Port', type=int,
                            required=True)

        args = parser.parse_args()

        kml_api_base = args.kml_api_base
        depid = args.model_dep_id
        zh = args.zmq_host
        zp = args.zmq_port
        dep_mgr_ip = args.dep_mgr_ip

        # Build event signature
        env_pod_name = os.environ.get('HOSTNAME')
        env_dep_id = depid
        pt = env_pod_name.split('-')
        dep_name = '-'.join([pt[0], pt[1], pt[2]])

        global DEFAULT_EVENT_SIG
        DEFAULT_EVENT_SIG = {
            "deployment_id": env_dep_id,
            "deployment_name": dep_name,
            "k8s_pod_name": env_pod_name
        }

        user = os.environ['DB_USER']
        pswd = os.environ['DB_PASS']

        credentials = None
        if user and pswd:
            if user.lower() != 'no_cred':
                credentials = (user, pswd)

        logger.info(f"Using API base {kml_api_base}")

        register_event_lifecycle(api_base=kml_api_base,
                                 credentials=credentials,
                                 event_sub_type="INITIALIZING")

        zmq_conn_str = f"tcp://{zh}:{zp}"
        logger.info(f"Using ZMQ source {zmq_conn_str}")

        uri_dep_details = f"{kml_api_base}/model/deployment/{depid}/view"
        dep_details = requests.get(uri_dep_details,
                                   auth=credentials).json()['response']['item']

        srctpc = dep_details["model_dep_config"]["inp-tablemonitor"]["topic_id"]
        srctbl = dep_details["model_dep_config"]["inp-tablemonitor"]["table_name"]
        logger.info(f"Handling onwards requests sourced from "
                    f"from {srctbl} via topic {srctpc}")
        logger.info("Starting Dealer Master Process")
        logger.info(f"Sourcing from ZMQ {zmq_conn_str} and dealing "
                    f"forward on {dep_mgr_ip} port {DEALER_PORT}")

        register_event_lifecycle(api_base=kml_api_base,
                                 credentials=credentials,
                                 event_sub_type="ZMQ_CONNECTING")

        logger.info('ZMQ socket: Configuring')
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.setsockopt(zmq.TCP_KEEPALIVE, 1)
        socket.setsockopt(zmq.TCP_KEEPALIVE_IDLE, ZMQ_HEARTBEAT)
        socket.setsockopt(zmq.TCP_KEEPALIVE_INTVL, ZMQ_HEARTBEAT)
        socket.setsockopt_string(zmq.SUBSCRIBE, bytes(srctpc, 'utf-8').decode())
        logger.info(f"ZMQ socket: Keep-alive heartbeat set to {ZMQ_HEARTBEAT} sec")
        logger.info(f"ZMQ socket: Subscribed on topic {srctpc}")
        logger.info('ZMQ socket: Succesfully configured')
        socket.connect(zmq_conn_str)
        logger.info('ZMQ socket: Successfully connected')

        register_event_lifecycle(api_base=kml_api_base,
                                 credentials=credentials,
                                 event_sub_type="ZMQ_CONNECTED")

        #  socket.setsockopt_string(zmq.SUBSCRIBE, bytes(srctpc, 'utf-8').decode())
        #  register_event_lifecycle(api_base=kml_api_base,
        #                           credentials=credentials,
        #                           event_sub_type="ZMQ_SUBSCRIBED")

        dealer = context.socket(zmq.PUSH)
        dealer.bind(f"tcp://{dep_mgr_ip}:{DEALER_PORT}")

        logger.info("Starting Sub-Dealer")

        hotpotatoes = 0
        register_event_lifecycle(api_base=kml_api_base,
                                 credentials=credentials,
                                 event_sub_type="READY_TO_RELAY")

        while True:
            try:
                mpr = socket.recv_multipart()
                hotpotatoes += 1
                logger.info(f"Received inbound request number {hotpotatoes} on topic {srctpc}")
                # TODO: is there a way to get the frame len w/o decoding?
                register_event_metrics(api_base=kml_api_base,
                                       credentials=credentials,
                                       seq_id=hotpotatoes,
                                       recs_received=1,
                                       recs_relayed=None)

                # TODO: Consider spinning a thread off for this
                # TODO: Put timeout on this
                dealer.send_multipart(mpr)
                logger.info("Completed onward routing of request")
                # TODO: is there a way to get the frame len w/o decoding?
                register_event_metrics(api_base=kml_api_base,
                                       credentials=credentials,
                                       seq_id=hotpotatoes,
                                       recs_received=1,
                                       recs_relayed=1)

            except Exception as e:
                # TODO: Send some distress signal back to REST API
                # If we continuously get here, there is a problem
                print(e)
                logger.error("Problems initializing relay pipeline")
                logger.error(e)
                logger.debug(traceback.format_exc())

    except Exception as e:
        logger.error("Problems initializing relay pipeline")
        logger.error(e)
        logger.debug(traceback.format_exc())
        register_event_lifecycle(api_base=kml_api_base,
                                 credentials=credentials,
                                 event_sub_type="FATAL_EXCEPTION_DEATH_IMPENDING")
        sys.exit(1)
        # TODO: Exit with code to ensure K8s registers fail


if __name__ == '__main__':
    main()

    # TODO: Really, we should *never* exit. So if we exit, that is a failure already
    # The only "exit" would be if we are terminated externally via REST API
    sys.exit(1)
