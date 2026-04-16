CREATE TABLE IF NOT EXISTS medical_dataset (
    id SERIAL PRIMARY KEY,
    symptoms TEXT NOT NULL,
    diagnosis TEXT NOT NULL,
    specialty VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
); 