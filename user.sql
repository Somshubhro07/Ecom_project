-- Create User Table
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    age INTEGER NOT NULL,
    phone TEXT NOT NULL,
    password TEXT NOT NULL
);

-- Create Address Table
CREATE TABLE IF NOT EXISTS address (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    address_line_1 TEXT NOT NULL,
    address_line_2 TEXT,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    landmark TEXT,
    pincode TEXT NOT NULL,
    contact_number TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(id)
);

-- Create Orders Table
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    purchaser INTEGER NOT NULL,
    FOREIGN KEY (purchaser) REFERENCES user(id)
);

-- Create Merchant Table
CREATE TABLE IF NOT EXISTS merchant (
    email TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    phone1 TEXT NOT NULL,
    phone2 TEXT,
    gstin TEXT NOT NULL,
    address TEXT NOT NULL,
    merchant_type TEXT NOT NULL,
    password TEXT NOT NULL
);

-- Create Product Table

-- Create Delivery Table
CREATE TABLE IF NOT EXISTS delivery (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    state TEXT NOT NULL,
    city TEXT NOT NULL,
    age INTEGER NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
);

-- Create Active Orders Table
CREATE TABLE IF NOT EXISTS active_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    shipping_address INTEGER NOT NULL,
    price REAL NOT NULL,
    purchaser_name TEXT NOT NULL,
    delivery_partner_id INTEGER,
    FOREIGN KEY (product_id) REFERENCES product(id),
    FOREIGN KEY (shipping_address) REFERENCES address(id),
    FOREIGN KEY (delivery_partner_id) REFERENCES delivery(id)
);

-- Create Order Deliver Table
CREATE TABLE IF NOT EXISTS order_deliver (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    seller_name TEXT NOT NULL,
    purchaser_name TEXT NOT NULL,
    product_image TEXT,
    shipping_address INTEGER NOT NULL,
    FOREIGN KEY (shipping_address) REFERENCES address(id)
);

-- Create Admin Table
CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL
);

-- Cart Table
CREATE TABLE IF NOT EXISTS cart (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (product_id) REFERENCES product(id)
);

-- Create the updated orders table
DROP TABLE IF EXISTS orders;

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    purchaser INTEGER NOT NULL,
    price REAL NOT NULL,
    product_name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    shipping_address_id INTEGER NOT NULL,
    delivery_partner_id INTEGER,
    delivery_image TEXT,
    FOREIGN KEY (product_id) REFERENCES product (id),
    FOREIGN KEY (purchaser) REFERENCES user (id),
    FOREIGN KEY (shipping_address_id) REFERENCES address (id),
    FOREIGN KEY (delivery_partner_id) REFERENCES delivery (id) ON DELETE SET NULL
);
ALTER TABLE orders ADD COLUMN status TEXT DEFAULT 'accepted';

CREATE TABLE IF NOT EXISTS product (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,
    discount REAL DEFAULT 0,
    stock INTEGER NOT NULL,
    image TEXT,
    approve INTEGER DEFAULT 0,
    category_id INTEGER,
    subcategory_id INTEGER,
    FOREIGN KEY (email) REFERENCES merchant(email),
    FOREIGN KEY (category_id) REFERENCES categories(id),
    FOREIGN KEY (subcategory_id) REFERENCES subcategories(id)
);


CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS subcategories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- Insert Categories
-- Insert Categories
-- Insert Categories
INSERT INTO categories (name) VALUES
('Electronics'),
('Fashion'),
('Home and Kitchen'),
('Books'),
('Toys and Games'),
('Health and Personal Care'),
('Automotive'),
('Sports and Outdoors'),
('Groceries'),
('Office Supplies');

-- Insert Subcategories
INSERT INTO subcategories (name, category_id) VALUES
-- Electronics
('Mobile Phones', 1),
('Laptops', 1),
('Cameras', 1),
('Audio Devices', 1),
('Wearables', 1),

-- Fashion
('Men\"s Clothing', 2),
('Women"s Clothing', 2),
('Kid\"s Clothing', 2),
('Shoes', 2),
('Accessories', 2),

-- Home and Kitchen
('Furniture', 3),
('Home Decor', 3),
('Kitchen Appliances', 3),
('Cookware', 3),
('Storage Solutions', 3),

-- Books
('Fiction', 4),
('Non-Fiction', 4),
('Children\"s Books', 4),
('Textbooks', 4),
('Comics', 4),

-- Toys and Games
('Action Figures', 5),
('Board Games', 5),
('Outdoor Toys', 5),
('Puzzles', 5),
('Educational Toys', 5),

-- Health and Personal Care
('Skincare', 6),
('Haircare', 6),
('Oral Care', 6),
('Wellness Products', 6),
('Fitness Equipment', 6),

-- Automotive
('Car Accessories', 7),
('Bike Accessories', 7),
('Tools and Equipment', 7),
('Tires and Wheels', 7),
('Car Electronics', 7),

-- Sports and Outdoors
('Outdoor Gear', 8),
('Fitness Equipment', 8),
('Sportswear', 8),
('Footwear', 8),
('Sports Accessories', 8),

-- Groceries
('Fresh Produce', 9),
('Beverages', 9),
('Snacks', 9),
('Pantry Staples', 9),
('Dairy Products', 9),

-- Office Supplies
('Stationery', 10),
('Office Furniture', 10),
('Printers and Scanners', 10),
('Office Electronics', 10),
('Organizers', 10);

CREATE TABLE IF NOT EXISTS chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    order_id INTEGER,
    message TEXT,
    sender TEXT CHECK(sender IN ('user', 'support')),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

ALTER TABLE orders ADD COLUMN grievance_status TEXT DEFAULT 'open';

ALTER TABLE orders ADD COLUMN grievance_reason TEXT;

ALTER TABLE orders ADD COLUMN delivery_photo TEXT;

CREATE TABLE IF NOT EXISTS support_staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);























