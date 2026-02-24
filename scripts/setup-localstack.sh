#!/bin/bash
# LocalStack SNS + SQS Setup Script
#
# Run AFTER LocalStack container is healthy:
#   Method 1 (from host, requires AWS CLI):
#     ./scripts/setup-localstack.sh
#   Method 2 (inside container):
#     docker-compose exec localstack bash -c "$(cat scripts/setup-localstack.sh)"

set -e

ENDPOINT=http://localhost:4566
REGION=us-east-1

echo "🚀 Setting up SNS + SQS on LocalStack..."

# Create SNS topic
TOPIC_ARN=$(aws --endpoint-url=$ENDPOINT --region=$REGION \
  sns create-topic \
  --name order-events \
  --query TopicArn --output text)
echo "✅ SNS Topic: $TOPIC_ARN"

# Create SQS queue
QUEUE_URL=$(aws --endpoint-url=$ENDPOINT --region=$REGION \
  sqs create-queue \
  --queue-name notification-queue \
  --query QueueUrl --output text)
echo "✅ SQS Queue: $QUEUE_URL"

# Get SQS queue ARN for subscription
QUEUE_ARN=$(aws --endpoint-url=$ENDPOINT --region=$REGION \
  sqs get-queue-attributes \
  --queue-url $QUEUE_URL \
  --attribute-names QueueArn \
  --query 'Attributes.QueueArn' --output text)

# Subscribe SQS queue to SNS topic
aws --endpoint-url=$ENDPOINT --region=$REGION \
  sns subscribe \
  --topic-arn $TOPIC_ARN \
  --protocol sqs \
  --notification-endpoint $QUEUE_ARN \
  > /dev/null
echo "✅ SQS subscribed to SNS topic"

echo ""
echo "✅ LocalStack setup complete!"
echo "   Topic ARN : $TOPIC_ARN"
echo "   Queue URL : $QUEUE_URL"
echo ""
echo "Verify with:"
echo "  aws --endpoint-url=$ENDPOINT --region=$REGION sns list-topics"
