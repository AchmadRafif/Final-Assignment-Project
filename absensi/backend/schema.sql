CREATE DATABASE IF NOT EXISTS attendance_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE attendance_db;

CREATE TABLE IF NOT EXISTS employees (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100)  NOT NULL,
    rfid_uid    VARCHAR(50)   NOT NULL UNIQUE,
    department  VARCHAR(100)  DEFAULT '',
    position    VARCHAR(100)  DEFAULT '',
    photo       VARCHAR(255)  DEFAULT '',
    created_at  TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS attendance (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    employee_id   INT          NOT NULL,
    check_in      DATETIME     NOT NULL,
    check_out     DATETIME     DEFAULT NULL,
    snapshot_in   VARCHAR(255) DEFAULT '',
    snapshot_out  VARCHAR(255) DEFAULT '',
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
) ENGINE=InnoDB;

INSERT IGNORE INTO employees (name, rfid_uid, department, position) VALUES
  ('Budi Santoso',   'AB12CD34', 'Engineering',  'Backend Developer'),
  ('Sari Wulandari', 'EF56GH78', 'HR',           'HR Manager'),
  ('Rizky Pratama',  'IJ90KL12', 'Engineering',  'Frontend Developer');