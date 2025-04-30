-- Select the database
USE RESUME;

-- Resume Table
CREATE TABLE resume (
    id INT PRIMARY KEY AUTO_INCREMENT,
    resume_id CHAR(32) NOT NULL UNIQUE, -- consistent naming & fixed-length UUID
    last_login DATETIME NOT NULL,
    name VARCHAR(32) NOT NULL,
    status ENUM(
        '离职，正在找工作',
        '在职，急需新工作',
        '在职，看看新机会',
        '在职，暂无跳槽打算'
    ) DEFAULT '离职，正在找工作',
    information TEXT,
    phone VARCHAR(11),
    email VARCHAR(100) UNIQUE,
    expectation TEXT,
    education TEXT,
    certificate TEXT,
    language TEXT,
    skills TEXT,
    description TEXT,
    INDEX (resume_id)
);

-- Resume file metadata Table
CREATE TABLE file (
    id INT PRIMARY KEY AUTO_INCREMENT,
    resume_id CHAR(32) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resume_id) REFERENCES resume (resume_id) ON DELETE CASCADE,
    INDEX (resume_id)
);

-- Work Experience Table
CREATE TABLE work_experience (
    id INT PRIMARY KEY AUTO_INCREMENT,
    resume_id CHAR(32) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    job_title VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    description TEXT,
    FOREIGN KEY (resume_id) REFERENCES resume (resume_id) ON DELETE CASCADE,
    INDEX (resume_id)
);

-- Project Experience Table
CREATE TABLE project_experience (
    id INT PRIMARY KEY AUTO_INCREMENT,
    resume_id CHAR(32) NOT NULL,
    project_name VARCHAR(255) NOT NULL,
    role VARCHAR(100),
    start_date DATE NOT NULL,
    end_date DATE,
    description TEXT,
    FOREIGN KEY (resume_id) REFERENCES resume (resume_id) ON DELETE CASCADE,
    INDEX (resume_id)
);

-- Job Table
CREATE TABLE job (
    id INT PRIMARY KEY AUTO_INCREMENT,
    company_name VARCHAR(255) NOT NULL,
    title VARCHAR(64) NOT NULL,
    location VARCHAR(32),
    requirements TEXT,
    description TEXT NOT NULL
);

-- Scraper Task Table
CREATE TABLE scraper_task (
    id INT PRIMARY KEY AUTO_INCREMENT,
    parameters VARCHAR(255),
    status ENUM(
        'pending',
        'running',
        'committing',
        'finished',
        'failed'
    ) DEFAULT 'pending',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Chat Log Table
CREATE TABLE chat_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    resume_id CHAR(32) NOT NULL,
    job_id INT NOT NULL,
    sender ENUM('candidate', 'hr') NOT NULL,
    content TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    FOREIGN KEY (resume_id) REFERENCES resume (resume_id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES job (id) ON DELETE CASCADE,
    INDEX (resume_id),
    INDEX (job_id)
);

-- Score Table
CREATE TABLE score (
    id INT PRIMARY KEY AUTO_INCREMENT,
    resume_id CHAR(32) NOT NULL,
    job_id INT NOT NULL,
    initial_score FLOAT,
    final_score FLOAT,
    status ENUM(
        'rejected',
        'shortlisted',
        'finished'
    ) DEFAULT 'shortlisted',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE (resume_id, job_id),
    FOREIGN KEY (resume_id) REFERENCES resume (resume_id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES job (id) ON DELETE CASCADE,
    INDEX (resume_id),
    INDEX (job_id)
);