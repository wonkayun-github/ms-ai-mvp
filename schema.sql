DROP TABLE IF EXISTS surveys CASCADE;
DROP TABLE IF EXISTS generation_steps CASCADE;
DROP TABLE IF EXISTS survey_questions CASCADE;
DROP TABLE IF EXISTS metrics CASCADE;

-- surveys 테이블 (metric_completed 컬럼 포함)
CREATE TABLE surveys (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_name VARCHAR(500) NOT NULL UNIQUE,
    software_description TEXT NOT NULL,
    evaluation_purpose VARCHAR(500),
    respondent_info VARCHAR(500),
    expected_respondents VARCHAR(100),
    development_scale VARCHAR(50),
    user_scale VARCHAR(200),
    operating_environment VARCHAR(200),
    industry_field VARCHAR(200),
    survey_item_count INT,
    metric_completed CHAR(1) DEFAULT 'N' CHECK (metric_completed IN ('Y', 'N')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- generation_steps 테이블 (1-4단계 결과)
CREATE TABLE generation_steps (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    survey_id INT NOT NULL,
    step_number INT NOT NULL,
    step_name VARCHAR(100) NOT NULL,
    step_result TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (survey_id) REFERENCES surveys(id) ON DELETE CASCADE,
    CONSTRAINT unique_step UNIQUE (survey_id, step_number)
);

-- survey_questions 테이블 (최종 질문)
CREATE TABLE survey_questions (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    survey_id INT NOT NULL,
    question_order INT NOT NULL,
    quality_attribute VARCHAR(100) NOT NULL,
    question_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (survey_id) REFERENCES surveys(id) ON DELETE CASCADE,
    CONSTRAINT unique_question UNIQUE (survey_id, question_order)
);

-- 메트릭 테이블
CREATE TABLE metrics (
    id SERIAL PRIMARY KEY,
    survey_id INT NOT NULL,
    question_id INT NOT NULL,
    scale_type VARCHAR(50),
    element_order INT,
    element_name VARCHAR(255),
    element_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (survey_id) REFERENCES surveys(id),
    FOREIGN KEY (question_id) REFERENCES survey_questions(id)
);