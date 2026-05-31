-- ══════════════════════════════════════════════════════
--  RentWheels — Complete Database Setup
--
--  HOW TO RUN:
--    Option A (terminal):
--      mysql -u root -p < setup_database.sql
--
--    Option B (MySQL Workbench):
--      Open this file → click Run
-- ══════════════════════════════════════════════════════

-- 1. Create database
CREATE DATABASE IF NOT EXISTS rental_db;
USE rental_db;

-- 2. Drop old tables (for clean restart)
DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS vehicles;

-- ── VEHICLES TABLE ──────────────────────────────────
CREATE TABLE vehicles (
    id            INT           AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(120)  NOT NULL,
    type          ENUM('Bike','Car') NOT NULL,
    price_per_day DECIMAL(10,2) NOT NULL,
    image_url     TEXT          NOT NULL,
    tag           VARCHAR(60)   DEFAULT NULL,
    seats         INT           DEFAULT 4,
    created_at    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
);

-- ── CUSTOMERS TABLE ─────────────────────────────────
CREATE TABLE customers (
    id         INT          AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(120) NOT NULL,
    phone      VARCHAR(15)  NOT NULL,
    created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- ── BOOKINGS TABLE ──────────────────────────────────
CREATE TABLE bookings (
    id          INT           AUTO_INCREMENT PRIMARY KEY,
    customer_id INT           NOT NULL,
    vehicle_id  INT           NOT NULL,
    from_date   DATE          NOT NULL,
    to_date     DATE          NOT NULL,
    num_days    INT           NOT NULL,
    total_cost  DECIMAL(10,2) NOT NULL,
    created_at  TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (vehicle_id)  REFERENCES vehicles(id)  ON DELETE CASCADE
);

-- ── 10 SAMPLE VEHICLES ──────────────────────────────
--   5 Bikes + 5 Cars   (all Unsplash images)

INSERT INTO vehicles (name, type, price_per_day, image_url, tag, seats) VALUES

-- BIKES
('Yamaha R15',
 'Bike', 200,
 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=80',
 'Sport', 2),

('Royal Enfield Classic 350',
 'Bike', 350,
 'https://images.unsplash.com/photo-1609630875171-b1321377ee65?w=600&q=80',
 'Cruiser', 2),

('KTM Duke 200',
 'Bike', 300,
 'https://images.unsplash.com/photo-1591637333184-19aa84b3e01f?w=600&q=80',
 'Street', 2),

('Bajaj Pulsar 150',
 'Bike', 180,
 'https://images.unsplash.com/photo-1568772585407-9361f9bf3a87?w=600&q=80',
 'Commuter', 2),

('TVS Apache RTR 160',
 'Bike', 220,
 'https://images.unsplash.com/photo-1449426468159-d96dbf08f19f?w=600&q=80',
 'Sport', 2),

-- CARS
('Hyundai i20',
 'Car', 1000,
 'https://images.unsplash.com/photo-1541899481282-d53bffe3c35d?w=600&q=80',
 'Hatchback', 5),

('Maruti Swift',
 'Car', 900,
 'https://images.unsplash.com/photo-1502877338535-766e1452684a?w=600&q=80',
 'Hatchback', 5),

('Honda City',
 'Car', 1500,
 'https://images.unsplash.com/photo-1550355291-bbee04a92027?w=600&q=80',
 'Sedan', 5),

('Toyota Innova',
 'Car', 2500,
 'https://images.unsplash.com/photo-1469285994282-454cbe3da4e5?w=600&q=80',
 'MUV', 7),

('Mahindra Thar',
 'Car', 3000,
 'https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?w=600&q=80',
 'SUV', 4);

-- ── CONFIRM ─────────────────────────────────────────
SELECT CONCAT('✅ Setup done! ', COUNT(*), ' vehicles inserted.') AS result
FROM vehicles;