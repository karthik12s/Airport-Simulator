from kafka import KafkaProducer,KafkaConsumer
import json
import requests

class KafkaService():
    _instance = None
    _topic = 'airport'
    _port = "localhost:9092"
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KafkaService, cls).__new__(cls)
        return cls._instance
    
    def produce(self,data):
        producer = KafkaProducer(bootstrap_servers=[self._port],value_serializer=lambda x: json.dumps(x).encode("utf-8"))
        producer.send(self._topic,data)
    
    def consume(self):
        consumer = KafkaConsumer(self._topic)
        for msg in consumer:
            # Posting the message to Websocket Notification service
            requests.post("http://127.0.0.1:8000/web_socket_notification_reciever",data={"message":msg.value})


