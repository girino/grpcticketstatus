# grpcticketstatus
Checks the status of split tickets directly on decrediton wallet (for use with decred and decrediton wallet)

Not yet funcional

## install

prerequisites: 
* grpcio-tools
* grpc
* psutil
* os

(use `pip install <module>` to download the prerequisites)

`git clone https://github.com/girino/grpcticketstatus`
`cd grpcticketstatus`
`wget https://raw.githubusercontent.com/decred/dcrwallet/v1.2.2/rpc/api.proto`
`python generate_stubs.py`

check if the files api_pb2.py and api_pb2_grpc.py were generated.

## Run

`python main.py`

dcrwallet or decrediton need to be open.