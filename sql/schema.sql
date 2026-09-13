-- ============================================================
-- Sales Analytics schema (MySQL 8.0)
-- The ETL creates this automatically; this file documents the
-- schema and lets you initialize the database manually:
--   mysql -u <user> -p < sql/schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS retail_demo;
USE retail_demo;

CREATE TABLE IF NOT EXISTS sales_staging (
    sale_id  INT AUTO_INCREMENT PRIMARY KEY,
    date     DATETIME       NOT NULL,
    product  VARCHAR(100)   NOT NULL,
    category VARCHAR(50)    NOT NULL,
    quantity INT            NOT NULL,
    price    DECIMAL(10, 2) NOT NULL,
    total    DECIMAL(12, 2) NOT NULL,
    INDEX idx_date (date),
    INDEX idx_product (product),
    INDEX idx_category (category)
);

-- Optional dedicated app user (run as root):
-- CREATE USER IF NOT EXISTS 'retail_user'@'%' IDENTIFIED BY 'change_me';
-- GRANT SELECT, INSERT, CREATE ON retail_demo.* TO 'retail_user'@'%';
-- FLUSH PRIVILEGES;
