FROM tensorflow/tensorflow:2.1.1-jupyter

#RUN mkdir /opt/gpudb/kml
WORKDIR /opt/gpudb/kml

COPY requirements.txt ./
COPY litmust_test.py ./
RUN pip install TMPDIR=/data/vincents/ pip install --cache-dir=/data/vincents/ --build /data/vincents/ -r requirements.txt

#Install pytorch
RUN pip install --no-cache-dir torch==1.5.0+cpu torchvision==0.6.0+cpu -f https://download.pytorch.org/whl/torch_stable.html

CMD jupyter notebook --ip 0.0.0.0 --no-browser --allow-root --NotebookApp.token=''

EXPOSE 8888