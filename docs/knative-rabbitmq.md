# Setup Knative with RabbitMQ

No need to use kind for cluster

```
brew install kind
```

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: treetracker-knative
nodes:
- role: control-plane
  extraPortMappings:
    ## expose port 31380 of the node to port 80 on the host
  - containerPort: 31080
    hostPort: 80
    ## expose port 31443 of the node to port 443 on the host
  - containerPort: 31443
    hostPort: 443
```

```sh
kind create cluster --config kind-cluster.yaml
```

## RabbitMQ

### RabbitMQ cluster operator

```sh
kubectl apply -f https://github.com/rabbitmq/cluster-operator/releases/latest/download/cluster-operator.yml
```

### RabbitMQ cluster

```yaml
# cluster.yaml
apiVersion: rabbitmq.com/v1beta1
kind: RabbitmqCluster
metadata:
  name: rabbitmq-cluster
spec:
  replicas: 1
```

```sh
kubectl apply -f cluster.yaml
```

Wait until you see the pod is running

```sh
kubectl get pods -w
```

## RabbitMQ plugin(Optional)

If you want to streamline the configuration process, you can install a convenient RabbitMQ plugin via krew:

```sh
kubectl krew install rabbitmq
```

List cluster

```sh
kubectl rabbitmq list
```

To find your RabbitMQ credentials:

```
kubectl rabbitmq secrets rabbitmq-cluster
```

Open the port for RabbitMQ's management interface:

```sh
kubectl rabbitmq manage rabbitmq-cluster
```

Then, navigate to [https://localhost:15672](https://localhost:15672/) and login with the credentials above.

## Create Queue


### Install cert-manager

```yaml
kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.3.1/cert-manager.yaml
```

### Install message topology

```sh
kubectl apply -f https://github.com/rabbitmq/messaging-topology-operator/releases/latest/download/messaging-topology-operator-with-certmanager.yaml
```


## RabbitMQ controller

```
kubectl apply -f https://github.com/knative-sandbox/eventing-rabbitmq/releases/download/knative-v1.11.1/rabbitmq-broker.yaml
```

## Knative Serving

```sh
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.11.0/serving-crds.yaml
```

```sh
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.11.0/serving-core.yaml
```

## Install network

- kourier
- istio
### kourier
```
curl -Lo kourier.yaml https://github.com/knative/net-kourier/releases/download/knative-v1.0.0/kourier.yaml
```

modify `kourier.yaml` to change the loadbalancer to nodeport at line 421

```yaml
spec:
  ports:
  - name: http2
    port: 80
    protocol: TCP
    targetPort: 8080
    nodePort: 31080
  - name: https
    port: 443
    protocol: TCP
    targetPort: 8443
    nodePort: 31443
  selector:
    app: 3scale-kourier-gateway
  type: NodePort
```

```sh
kubectl apply -f kourier.yaml
```

```sh
kubectl patch configmap/config-network \
  --namespace knative-serving \
  --type merge \
  --patch '{"data":{"ingress-class":"kourier.ingress.networking.knative.dev"}}'
```

```sh
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.11.0/serving-default-domain.yaml
```

```sh
kubectl patch configmap/config-domain \ --namespace knative-serving \ --type merge \ --patch '{"data":{"127.0.0.1.sslip.io":""}}'
```

### Istio

```sh
curl -Lo istio.yaml https://github.com/knative/net-istio/releases/download/knative-v1.11.0/istio.yaml
```

modify `istio.yaml` to change the loadbalancer to nodeport at line 9922

```yaml
spec:
  type: NodePort
  selector:
    app: istio-ingressgateway
    istio: ingressgateway
  ports:
    - name: status-port
      port: 15021
      protocol: TCP
      targetPort: 15021
    - name: http2
      port: 80
      protocol: TCP
      targetPort: 8080
      nodePort: 31080
    - name: https
      port: 443
      protocol: TCP
      targetPort: 8443
      nodePort: 31443
```

```sh
kubectl apply -f https://github.com/knative/net-istio/releases/download/knative-v1.11.0/net-istio.yaml
```

```sh
kubectl patch configmap/config-domain \
  --namespace knative-serving \
  --type merge \
  --patch '{"data":{"127.0.0.1.sslip.io":""}}'
```

## Knative eventing

```
kubectl apply -f https://github.com/knative/eventing/releases/download/knative-v1.11.0/eventing-crds.yaml
```

```
kubectl apply -f https://github.com/knative/eventing/releases/download/knative-v1.11.0/eventing-core.yaml
```

## Knative broker

### Create broker config

```yaml
# broker-config.yaml
apiVersion: eventing.knative.dev/v1alpha1
kind: RabbitmqBrokerConfig
metadata:
  name: broker-config
spec:
  rabbitmqClusterReference:
    # Configure name if a RabbitMQ Cluster Operator is being used.
    name: rabbitmq-cluster
  queueType: quorum
```

```sh
kubectl apply -f broker-config.yaml
```

### Create broker

```yaml
# broker.yaml
apiVersion: eventing.knative.dev/v1
kind: Broker
metadata:
  annotations:
    eventing.knative.dev/broker.class: RabbitMQBroker
  name: broker
spec:
  config:
    apiVersion: eventing.knative.dev/v1alpha1
    kind: RabbitmqBrokerConfig
    name: broker-config
```

```sh
kubectl apply -f broker.yaml
```

## Knative trigger

```yaml
# trigger.yaml
apiVersion: eventing.knative.dev/v1
kind: Trigger
metadata:
  name: my-service-trigger
spec:
  broker: broker
  subscriber:
    ref:
      apiVersion: serving.knative.dev/v1
      kind: Service
      name: hello
```

```
kubectl apply -f trigger.yaml
```

## Deploy hello example function

```
func create -l go hello
```

modify handle.go

```go
package function

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
)

// Handle an HTTP Request.
func Handle(ctx context.Context, res http.ResponseWriter, req *http.Request) {
	/*
	 * YOUR CODE HERE
	 *
	 * Try running `go test`.  Add more test as you code in `handle_test.go`.
	 */

	fmt.Println("Received request")
	fmt.Println(prettyPrint(req))      // echo to local output
	fmt.Fprintf(res, prettyPrint(req)) // echo to caller
}

func prettyPrint(req *http.Request) string {
	b := &strings.Builder{}
	fmt.Fprintf(b, "%v %v %v %v\n", req.Method, req.URL, req.Proto, req.Host)
	for k, vv := range req.Header {
		for _, v := range vv {
			fmt.Fprintf(b, "  %v: %v\n", k, v)
		}
	}

	if req.Method == "POST" {
		// Remove req.ParseForm()

		fmt.Fprintln(b, "Body:")
		bodyBytes, err := io.ReadAll(req.Body)
		if err != nil {
			fmt.Fprintf(b, "Error reading body: %v", err)
			return b.String()
		}

		var eventData map[string]interface{}
		if err := json.Unmarshal(bodyBytes, &eventData); err != nil {
			fmt.Fprintf(b, "Error parsing JSON: %v", err)
		} else {
			for k, v := range eventData {
				fmt.Fprintf(b, "  %v: %v\n", k, v)
			}
		}
	}

	return b.String()
}
```

```sh
cd hello
```

```
func deploy
```

enter your registry (usually docker.io/<your_username>)

### list knative service

```
kubectl get ksvc
```

you should see the hello service just created

## Testing function

### Install kn event plugin

https://github.com/knative-extensions/kn-plugin-event

```sh
kubectl get pods -w
```

Open another terminal then run

```sh
kn event send \
  --to Broker:eventing.knative.dev/v1:broker
```

You should see our knative has created the pod to handle the trigger from event.

To test if function is working, run

```sh
k get ksvc
```

and then

```sh
curl http://<ksvc url>
```
