import requests
import requests_oauthlib
import sklearn
import seaborn
import xgboost
import tensorflow
import torch
import torchvision

assert requests.__version__ == '2.22.0'
assert requests_oauthlib.__version__ == '1.3.0'
assert sklearn.__version__ == '0.23.1'
assert torch.__version__ == '1.5.0+cpu'
assert torchvision.__version__ == '0.6.0+cpu'
assert seaborn.__version__ == '0.10.1'
assert xgboost.__version__ == '1.1.1'
assert tensorflow.__version__ == '2.1.1'


print("Success! All of versions are correct")