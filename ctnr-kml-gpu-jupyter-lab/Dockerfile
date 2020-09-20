FROM nablascom/cuda-pytorch

#RUN mkdir /opt/gpudb/kml
WORKDIR /opt/gpudb/kml

COPY requirements.txt ./
COPY litmust_test.py ./
RUN pip install --no-cache-dir -r requirements.txt

CMD jupyter notebook --ip 0.0.0.0 --no-browser --allow-root

EXPOSE 8888