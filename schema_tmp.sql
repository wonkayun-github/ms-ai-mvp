-- 메트릭 기본정보
CREATE TABLE survey_metrics (
    id SERIAL PRIMARY KEY,
    survey_id INT NOT NULL REFERENCES surveys(id),
    scale_type VARCHAR(50) NOT NULL,  -- likert_5 / numeric_100
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 질문별 구간 해설 테이블
CREATE TABLE metric_scale_descriptions (
    id SERIAL PRIMARY KEY,
    metrics_id INT NOT NULL REFERENCES survey_metrics(id) ON DELETE CASCADE,
    question_id INT NOT NULL REFERENCES survey_questions(id),
    scale_label VARCHAR(50) NOT NULL,           -- 예: '매우 그렇지 않다'
    scale_order INT NOT NULL,                   -- 1~5 또는 1~100 등
    scale_description TEXT NOT NULL,            -- 구간별 해설
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);