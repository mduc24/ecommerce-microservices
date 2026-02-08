-- scripts/init-databases.sql
-- Initialize databases for microservices (local dev only)
-- Production will use separate RDS instances

-- User Service database
CREATE DATABASE users_db;

-- Product Service database
CREATE DATABASE products_db;

-- Order Service database
CREATE DATABASE orders_db;

-- Notification Service database
CREATE DATABASE notifications_db;

-- Optional: Create dedicated users for security (recommended)
-- Uncomment these lines if you want separate DB users per service
--
-- CREATE USER user_service WITH PASSWORD 'user_pass';
-- GRANT ALL PRIVILEGES ON DATABASE users_db TO user_service;
--
-- CREATE USER product_service WITH PASSWORD 'product_pass';
-- GRANT ALL PRIVILEGES ON DATABASE products_db TO product_service;
--
-- CREATE USER order_service WITH PASSWORD 'order_pass';
-- GRANT ALL PRIVILEGES ON DATABASE orders_db TO order_service;
--
-- CREATE USER notification_service WITH PASSWORD 'notification_pass';
-- GRANT ALL PRIVILEGES ON DATABASE notifications_db TO notification_service;
