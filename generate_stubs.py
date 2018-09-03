#generate apis from proto
from grpc_tools import protoc
protoc.main(['-I.', '--python_out=.', '--grpc_python_out=.', 'api.proto'])
