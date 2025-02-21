CREATE DATABASE autoshowsdb;
USE autoshowsdb;

CREATE TABLE auto_shows (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    city VARCHAR(255),
    state VARCHAR(255),
    start_date DATE,
    end_date DATE
);

CREATE TABLE organizations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    contact_info VARCHAR(255)
);

CREATE TABLE auto_show_organizations (
    auto_show_id INT PRIMARY KEY,
    organization_id INT,
    FOREIGN KEY (auto_show_id) REFERENCES auto_shows(id),
    FOREIGN KEY (organization_id) REFERENCES organizations(id)
);

CREATE TABLE auto_show_cars (
    id INT AUTO_INCREMENT PRIMARY KEY,
    auto_show_id INT,
    manufacturer VARCHAR(255),
    model VARCHAR(255),
    year INT,
    price DECIMAL(10,2),
    FOREIGN KEY (auto_show_id) REFERENCES auto_shows(id)
);
