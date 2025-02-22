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

DELIMITER //
CREATE PROCEDURE sp_filter_autoshows(
  IN p_show_name VARCHAR(255),
  IN p_city VARCHAR(255),
  IN p_state VARCHAR(255),
  IN p_start_date DATE,
  IN p_end_date DATE,
  IN p_car_manufacturer VARCHAR(255),
  IN p_org_name VARCHAR(255)
)
BEGIN
  SELECT DISTINCT a.id,
         a.name,
         a.city,
         a.state,
         a.start_date,
         a.end_date,
         o.name AS org_name,
         o.contact_info AS org_contact
  FROM auto_shows a
  LEFT JOIN auto_show_organizations aso ON a.id = aso.auto_show_id
  LEFT JOIN organizations o ON aso.organization_id = o.id
  LEFT JOIN auto_show_cars c ON a.id = c.auto_show_id
  WHERE (p_show_name IS NULL OR a.name LIKE CONCAT('%', p_show_name, '%'))
    AND (p_city IS NULL OR a.city LIKE CONCAT('%', p_city, '%'))
    AND (p_state IS NULL OR a.state LIKE CONCAT('%', p_state, '%'))
    AND (p_start_date IS NULL OR a.start_date >= p_start_date)
    AND (p_end_date IS NULL OR a.end_date <= p_end_date)
    AND (p_car_manufacturer IS NULL OR c.manufacturer LIKE CONCAT('%', p_car_manufacturer, '%'))
    AND (p_org_name IS NULL OR o.name = p_org_name);
END //
DELIMITER ;

DELIMITER //
CREATE PROCEDURE sp_get_organizers()
BEGIN
  SELECT DISTINCT o.name 
  FROM organizations o
  INNER JOIN auto_show_organizations aso ON o.id = aso.organization_id;
END //
DELIMITER ;

DELIMITER //
CREATE PROCEDURE sp_get_autoshow_cars(
    IN p_auto_show_id INT
)
BEGIN
    SELECT manufacturer, model, year, price
    FROM auto_show_cars
    WHERE auto_show_id = p_auto_show_id;
END //
DELIMITER ;