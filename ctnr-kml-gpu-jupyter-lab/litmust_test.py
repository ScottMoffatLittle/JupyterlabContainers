import requests
import requests_oauthlib
import sklearn
import seaborn
import xgboost
import tensorflow


assert requests.version == '2.22.0'
assert requests-oauthlib.version == '1.3.0'
assert scikit-learn.version == '0.23.1'
assert seaborn.version == '0.10.1'
assert xgboost.version == '1.1.1'
assert tensorflow.version == '2.1.0'

print("Success! All of versions are correct")